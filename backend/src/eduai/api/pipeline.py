from fastapi import APIRouter, Body, HTTPException
import subprocess
import sys
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

router = APIRouter()

SCRIPTS_DIR = (
    Path(__file__).resolve()
    .parents[1]      # eduai/
    / "scripts"
)

ALLOWED = {
    "step0": "step0_inbox.py",
    "step1": "step1_raw.py",
    "step2": "step2_staging.py",
    "step3": "step3_processed_files.py",
    "step4": "step3_processed_qdrant.py",
}


class RunStepBody(BaseModel):
    """Chỉ chạy trên các thư mục được chọn; để trống = chạy toàn bộ. force_rerun = chạy lại kể cả đã làm rồi. collection_name = chỉ step4 (Qdrant). qdrant_url = chỉ step4 (insert vào Qdrant Service này)."""
    only_folders: Optional[list[str]] = None
    force_rerun: Optional[bool] = False
    collection_name: Optional[str] = None
    qdrant_url: Optional[str] = None


def _list_folders_for_step(step: str) -> list[str]:
    """Trả về danh sách tên thư mục (domain / file_hash) cho bước pipeline."""
    from eduai.config import paths

    out = []
    try:
        if step == "step0":
            inbox = paths.inbox_path()
            if inbox.exists():
                out = [d.name for d in sorted(inbox.iterdir()) if d.is_dir() and not d.name.startswith(".")]
        elif step == "step1":
            raw = paths.raw_path()
            if raw.exists():
                out = sorted({p.stem for p in raw.rglob("*.pdf")})
        elif step == "step2":
            staging = paths.staging_path()
            if staging.exists():
                # 200_staging: <domain>/<file_hash>/ hoặc (cũ) <file_hash>/
                domain_names = []
                file_hashes_flat = []
                for entry in staging.iterdir():
                    if not entry.is_dir() or entry.name.startswith("."):
                        continue
                    if (entry / "validation.json").exists():
                        file_hashes_flat.append(entry.name)
                    else:
                        domain_names.append(entry.name)
                # Ưu tiên trả về thư mục cha (domain) để chọn; không có thì trả về file_hash (cấu trúc cũ)
                out = sorted(domain_names) if domain_names else sorted(file_hashes_flat)
        elif step == "step3":
            processed = paths.processed_path()
            if processed.exists():
                # 300_processed: <domain>/<file_hash>/ hoặc (cũ) <file_hash>/
                file_hashes = set()
                for entry in processed.iterdir():
                    if not entry.is_dir() or entry.name.startswith("."):
                        continue
                    if (entry / "chunks.json").exists():
                        file_hashes.add(entry.name)
                    else:
                        for sub in entry.iterdir():
                            if sub.is_dir() and (sub / "chunks.json").exists():
                                file_hashes.add(sub.name)
                out = sorted(file_hashes)
        elif step == "step4":
            emb = paths.embeddings_path()
            if emb.exists():
                # 400_embeddings: <domain>/<file_hash>/ hoặc (cũ) <file_hash>/
                domain_names = []
                file_hashes_flat = []
                for entry in emb.iterdir():
                    if not entry.is_dir() or entry.name.startswith("."):
                        continue
                    if (entry / "embedding.npy").exists():
                        file_hashes_flat.append(entry.name)
                    else:
                        domain_names.append(entry.name)
                out = sorted(domain_names) if domain_names else sorted(file_hashes_flat)
    except Exception:
        pass
    return out


@router.get("/folders/{step}")
def list_folders(step: str) -> dict:
    """Danh sách thư mục có thể chọn để chạy bước pipeline (chọn subset thay vì chạy toàn bộ)."""
    if step not in ALLOWED:
        raise HTTPException(status_code=400, detail="Invalid step")
    folders = _list_folders_for_step(step)
    return {"step": step, "folders": folders}


@router.post("/run/{step}")
def run_step(step: str, body: Optional[RunStepBody] = Body(default=None)):
    if step not in ALLOWED:
        raise HTTPException(status_code=400, detail="Invalid step")

    script_path = SCRIPTS_DIR / ALLOWED[step]
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Script not found: {script_path}")

    env = os.environ.copy()
    env["PYTHONPATH"] = env.get("PYTHONPATH", "/app/src")
    if body and body.only_folders:
        env["PIPELINE_ONLY_FOLDERS"] = ",".join(body.only_folders)
    if body and body.force_rerun:
        env["PIPELINE_FORCE_RERUN"] = "1"
    if body and body.collection_name and body.collection_name.strip():
        env["PIPELINE_QDRANT_COLLECTION"] = body.collection_name.strip()
    if body and body.qdrant_url and body.qdrant_url.strip() and step == "step4":
        # Truyền Qdrant Service cho script step3_processed_qdrant (host:port hoặc URL)
        u = body.qdrant_url.strip()
        if u.startswith("http://"):
            u = u[7:]
        elif u.startswith("https://"):
            u = u[8:]
        if ":" in u:
            host, port = u.split(":", 1)
            env["QDRANT_HOST"] = host.strip()
            env["QDRANT_PORT"] = port.strip()
        else:
            env["QDRANT_HOST"] = u
            env["QDRANT_PORT"] = "6333"

    # Truyền đúng DATA_BASE_PATH mà backend đang dùng (tránh subprocess nhận /data)
    from eduai.runtime.config import runtime_config
    try:
        env["EDUAI_DATA_BASE_PATH"] = str(runtime_config.get_data_base_path())
        env["EDUAI_MODE"] = os.getenv("EDUAI_MODE", "")
    except RuntimeError:
        pass

    try:
        p = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            env=env,
            cwd=Path(__file__).resolve().parents[3],
            timeout=60 * 60,  # 1h tuỳ nhu cầu
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Pipeline step timed out")

    return {
        "step": step,
        "script": ALLOWED[step],
        "returncode": p.returncode,
        "stdout": p.stdout,
        "stderr": p.stderr,
    }
