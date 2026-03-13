from fastapi import APIRouter, Body, HTTPException

from lakeflow.i18n import i18n_detail
import subprocess
import sys
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from lakeflow.services.ollama_embed_service import EMBED_MODEL

router = APIRouter()

# Default embed models (Ollama); override via EMBED_MODEL_OPTIONS env (comma-separated)
DEFAULT_EMBED_MODELS = [
    "qwen3-embedding:8b",
    "nomic-embed-text",
    "mxbai-embed-large",
    "all-minilm",
]

SCRIPTS_DIR = (
    Path(__file__).resolve()
    .parents[1]      # lakeflow/
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
    """Run only on selected folders; leave empty = run all. force_rerun = run again even if already done. collection_name = step4 only (Qdrant). qdrant_url = step4 only. embed_model = step3 only (Ollama embed model, e.g. qwen3-embedding:8b, nomic-embed-text)."""
    only_folders: Optional[list[str]] = None
    force_rerun: Optional[bool] = False
    collection_name: Optional[str] = None
    qdrant_url: Optional[str] = None
    embed_model: Optional[str] = None


def _list_folders_for_step(step: str) -> list[str]:
    """Return list of folder paths (relative, can be nested e.g. 'Library/Quy định hướng dẫn') for the pipeline step."""
    from lakeflow.config import paths

    out = []
    try:
        if step == "step0":
            inbox = paths.inbox_path()
            if inbox.exists():
                out = [d.name for d in sorted(inbox.iterdir()) if d.is_dir() and not d.name.startswith(".")]
        elif step == "step1":
            raw = paths.raw_path()
            if raw.exists():
                out = sorted({p.stem for p in raw.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"})
        elif step == "step2":
            staging = paths.staging_path()
            if staging.exists():
                # Collect all parent paths that contain validation.json (nested structure)
                parent_dirs = set()
                for path in staging.rglob("validation.json"):
                    if path.is_file():
                        d = path.parent
                        if d != staging:
                            parent_dirs.add(str(d.parent.relative_to(staging)).replace("\\", "/"))
                out = sorted(parent_dirs) if parent_dirs else []
        elif step == "step3":
            processed = paths.processed_path()
            if processed.exists():
                parent_dirs = set()
                for path in processed.rglob("chunks.json"):
                    if path.is_file():
                        d = path.parent
                        if d != processed:
                            parent_dirs.add(str(d.parent.relative_to(processed)).replace("\\", "/"))
                out = sorted(parent_dirs) if parent_dirs else []
        elif step == "step4":
            emb = paths.embeddings_path()
            if emb.exists():
                parent_dirs = set()
                for path in emb.rglob("embedding.npy"):
                    if path.is_file():
                        d = path.parent
                        if d != emb:
                            parent_dirs.add(str(d.parent.relative_to(emb)).replace("\\", "/"))
                out = sorted(parent_dirs) if parent_dirs else []
    except Exception:
        pass
    return out


def _get_embed_models() -> list[str]:
    """Return list of embed model names for step3 selection."""
    raw = os.getenv("EMBED_MODEL_OPTIONS", "").strip()
    if raw:
        return [m.strip() for m in raw.split(",") if m.strip()]
    return DEFAULT_EMBED_MODELS


@router.get("/embed-models")
def list_embed_models() -> dict:
    """List of embed models for step3. Default from EMBED_MODEL_OPTIONS env or built-in list."""
    models = _get_embed_models()
    return {"models": models, "default": EMBED_MODEL}


@router.get("/folders/{step}")
def list_folders(step: str) -> dict:
    """List of folders that can be selected to run the pipeline step (select subset instead of running all)."""
    if step not in ALLOWED:
        raise HTTPException(status_code=400, detail=i18n_detail("pipeline.invalid_step"))
    folders = _list_folders_for_step(step)
    return {"step": step, "folders": folders}


@router.post("/run/{step}")
def run_step(step: str, body: Optional[RunStepBody] = Body(default=None)):
    if step not in ALLOWED:
        raise HTTPException(status_code=400, detail=i18n_detail("pipeline.invalid_step"))

    script_path = SCRIPTS_DIR / ALLOWED[step]
    if not script_path.exists():
        raise HTTPException(
            status_code=404,
            detail=i18n_detail("pipeline.script_not_found", script_path=str(script_path)),
        )

    env = os.environ.copy()
    env["PYTHONPATH"] = env.get("PYTHONPATH", "/app/src")
    if body and body.only_folders:
        env["PIPELINE_ONLY_FOLDERS"] = ",".join(body.only_folders)
    if body and body.force_rerun:
        env["PIPELINE_FORCE_RERUN"] = "1"
    if body and body.collection_name and body.collection_name.strip():
        env["PIPELINE_QDRANT_COLLECTION"] = body.collection_name.strip()
    if body and body.embed_model and body.embed_model.strip() and step == "step3":
        env["PIPELINE_EMBED_MODEL"] = body.embed_model.strip()
    if body and body.qdrant_url and body.qdrant_url.strip() and step == "step4":
        # Pass Qdrant service to step3_processed_qdrant script (host:port or URL)
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

    # Pass correct DATA_BASE_PATH that backend uses (avoid subprocess receiving /data)
    from lakeflow.runtime.config import runtime_config
    try:
        env["LAKE_ROOT"] = str(runtime_config.get_data_base_path())
        env["LAKEFLOW_MODE"] = os.getenv("LAKEFLOW_MODE", "")
    except RuntimeError:
        pass

    try:
        p = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            env=env,
            cwd=Path(__file__).resolve().parents[3],
            timeout=60 * 60,  # 1h as needed
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail=i18n_detail("pipeline.timeout"))

    return {
        "step": step,
        "script": ALLOWED[step],
        "returncode": p.returncode,
        "stdout": p.stdout,
        "stderr": p.stderr,
    }
