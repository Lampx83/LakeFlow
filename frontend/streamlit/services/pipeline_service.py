import requests
from config.settings import API_BASE, DATA_ROOT
from pathlib import Path
from typing import Optional

# Bước nào dùng cây thư mục (chọn con/cháu); bước còn lại dùng danh sách phẳng (file_hash)
STEPS_WITH_TREE = ("step0", "step1", "step2", "step3", "step4")


def get_pipeline_folder_children(step: str, relative_path: str = "") -> list[tuple[str, str]]:
    """
    Trả về danh sách thư mục con: [(tên hiển thị, full_relative_path)].
    Dùng để render cây thư mục cho step0..step4.
    step2: 200_staging/<domain>/<file_hash>/ hoặc (cũ) 200_staging/<file_hash>/
    step3: 300_processed/<domain>/<file_hash>/ hoặc (cũ) 300_processed/<file_hash>/
    step4: 400_embeddings/<domain>/<file_hash>/ hoặc (cũ) 400_embeddings/<file_hash>/
    """
    root = Path(DATA_ROOT)
    if step == "step0":
        base = root / "000_inbox"
    elif step == "step1":
        base = root / "100_raw"
    elif step == "step2":
        base = root / "200_staging"
    elif step == "step3":
        base = root / "300_processed"
    elif step == "step4":
        base = root / "400_embeddings"
    else:
        return []
    if not base.exists():
        return []
    path = base / relative_path if relative_path else base
    if not path.exists() or not path.is_dir():
        return []
    out = []
    try:
        for d in sorted(path.iterdir(), key=lambda p: p.name.lower()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            full_rel = f"{relative_path}/{d.name}" if relative_path else d.name
            out.append((d.name, full_rel))
    except (PermissionError, OSError):
        pass
    return out


def _get_pipeline_folders_fallback(step: str) -> list[str]:
    """
    Fallback: lấy danh sách thư mục từ DATA_ROOT (cùng cấu hình Data Lake Explorer).
    Dùng khi backend chưa có API GET /pipeline/folders hoặc trả 404.
    """
    root = Path(DATA_ROOT)
    out = []
    try:
        if step == "step0":
            p = root / "000_inbox"
            if p.exists():
                out = sorted([d.name for d in p.iterdir() if d.is_dir() and not d.name.startswith(".")])
        elif step == "step1":
            p = root / "100_raw"
            if p.exists():
                out = sorted({f.stem for f in p.rglob("*.pdf")})
        elif step == "step2":
            p = root / "200_staging"
            if p.exists():
                out = sorted([d.name for d in p.iterdir() if d.is_dir() and not d.name.startswith(".")])
        elif step == "step3":
            p = root / "300_processed"
            if p.exists():
                out = sorted([d.name for d in p.iterdir() if d.is_dir() and not d.name.startswith(".")])
        elif step == "step4":
            p = root / "400_embeddings"
            if p.exists():
                out = sorted([d.name for d in p.iterdir() if d.is_dir() and not d.name.startswith(".")])
    except Exception:
        pass
    return out


def get_pipeline_folders(step: str, token: Optional[str] = None) -> list[str]:
    """Lấy danh sách thư mục có thể chọn cho bước pipeline (API, fallback từ DATA_ROOT nếu 404)."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = requests.get(
            f"{API_BASE}/pipeline/folders/{step}",
            headers=headers,
            timeout=30,
        )
        if resp.status_code == 404:
            return _get_pipeline_folders_fallback(step)
        resp.raise_for_status()
        return resp.json().get("folders", [])
    except requests.HTTPError:
        raise
    except Exception:
        return _get_pipeline_folders_fallback(step)


def list_qdrant_collections(token: Optional[str] = None) -> list[str]:
    """Lấy danh sách tên collection có sẵn trong Qdrant (dùng cho bước Qdrant Indexing)."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = requests.get(
            f"{API_BASE}/qdrant/collections",
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        raw = resp.json().get("collections", [])
        return [c.get("name", "") for c in raw if c.get("name")]
    except Exception:
        return []


def run_pipeline_step(
    step: str,
    only_folders: Optional[list[str]] = None,
    force_rerun: bool = False,
    collection_name: Optional[str] = None,
    qdrant_url: Optional[str] = None,
    token: Optional[str] = None,
) -> dict:
    """Chạy bước pipeline; only_folders = None hoặc [] = chạy toàn bộ; force_rerun = chạy lại kể cả đã làm; collection_name / qdrant_url = chỉ step4 (Qdrant)."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    body = {}
    if only_folders:
        body["only_folders"] = only_folders
    if force_rerun:
        body["force_rerun"] = True
    if collection_name and collection_name.strip():
        body["collection_name"] = collection_name.strip()
    if step == "step4" and qdrant_url and qdrant_url.strip():
        body["qdrant_url"] = qdrant_url.strip()
    resp = requests.post(
        f"{API_BASE}/pipeline/run/{step}",
        json=body if body else None,
        headers=headers,
        timeout=3600,
    )
    resp.raise_for_status()
    return resp.json()
