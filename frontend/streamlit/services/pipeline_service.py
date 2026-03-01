import hashlib
import sqlite3
from pathlib import Path
from typing import Optional

import requests

from config.settings import API_BASE, DATA_ROOT
from utils.sqlite_viewer import copy_db_to_temp

# Which steps use directory tree (select children); others use flat list (file_hash)
STEPS_WITH_TREE = ("step0", "step1", "step2", "step3", "step4")


def get_pipeline_folder_children(step: str, relative_path: str = "") -> list[tuple[str, str]]:
    """
    Return list of child directories: [(display_name, full_relative_path)].
    Used to render directory tree for step0..step4.
    step2: 200_staging/<domain>/<file_hash>/ or (legacy) 200_staging/<file_hash>/
    step3: 300_processed/<domain>/<file_hash>/ or (legacy) 300_processed/<file_hash>/
    step4: 400_embeddings/<domain>/<file_hash>/ or (legacy) 400_embeddings/<file_hash>/
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


def get_pipeline_folder_files(step: str, relative_path: str = "") -> list[tuple[str, int]]:
    """
    Return list of files in directory: [(file_name, size_bytes)].
    relative_path = "" is zone root; "domain" or "domain/hash" is child.
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
        for p in sorted(path.iterdir(), key=lambda x: x.name.lower()):
            if p.name.startswith("."):
                continue
            if p.is_file():
                try:
                    out.append((p.name, p.stat().st_size))
                except OSError:
                    out.append((p.name, 0))
    except (PermissionError, OSError):
        pass
    return out


def get_pipeline_file_step_done(step: str, relative_path: str, file_name: str) -> str:
    """
    Return "✓" if file (or current directory) has been processed at this step, "" if not, "?" if unknown (e.g. step4).
    step0: inbox file → ingested (hash in raw_objects)
    step1: file in 100_raw → staged (200_staging/.../validation.json)
    step2: file in 200_staging → processed (300_processed/.../chunks.json) — by directory
    step3: file in 300_processed → embedded (400_embeddings/.../embedding.npy) — by directory
    step4: no catalog → "?"
    """
    root = Path(DATA_ROOT)
    rel = relative_path.strip("/").replace("\\", "/")
    parts = [p for p in rel.split("/") if p] if rel else []

    if step == "step0":
        base = root / "000_inbox"
        dir_path = (base / relative_path) if relative_path else base
        file_path = dir_path / file_name
        if not file_path.is_file():
            return ""
        try:
            h = hashlib.sha256()
            with file_path.open("rb") as f:
                while chunk := f.read(1024 * 1024):
                    h.update(chunk)
            file_hash = h.hexdigest()
        except (OSError, PermissionError):
            return ""
        db = root / "500_catalog" / "catalog.sqlite"
        if not db.exists():
            return ""
        temp_path = None
        try:
            temp_path = copy_db_to_temp(db)
            conn = sqlite3.connect(str(temp_path), timeout=5)
            cur = conn.execute("SELECT 1 FROM raw_objects WHERE hash = ? LIMIT 1", (file_hash,))
            out = "✓" if cur.fetchone() else ""
            conn.close()
            return out
        except Exception:
            return ""
        finally:
            if temp_path and Path(temp_path).exists():
                try:
                    Path(temp_path).unlink()
                except OSError:
                    pass

    if step == "step1":
        file_hash = Path(file_name).stem
        staging_dir = root / "200_staging" / relative_path / file_hash if relative_path else root / "200_staging" / file_hash
        alt = root / "200_staging" / file_hash
        if (staging_dir / "validation.json").exists() or (alt / "validation.json").exists():
            return "✓"
        return ""

    if step == "step2":
        # Has 200_staging/relative_path run step 2 (→ 300_processed) yet
        if not relative_path:
            return ""
        check = root / "300_processed" / relative_path / "chunks.json"
        alt = root / "300_processed" / parts[-1] / "chunks.json" if len(parts) == 1 else None
        if check.exists() or (alt and alt.exists()):
            return "✓"
        return ""

    if step == "step3":
        if not relative_path:
            return ""
        check = root / "400_embeddings" / relative_path / "embedding.npy"
        alt = root / "400_embeddings" / parts[-1] / "embedding.npy" if len(parts) == 1 else None
        if check.exists() or (alt and alt.exists()):
            return "✓"
        return ""

    if step == "step4":
        return "?"
    return ""


def _get_pipeline_folders_fallback(step: str) -> list[str]:
    """
    Fallback: get folder list from DATA_ROOT (same config as Data Lake Explorer).
    Used when backend lacks GET /pipeline/folders API or returns 404.
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
    """Get selectable folder list for pipeline step (API, fallback from DATA_ROOT if 404)."""
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
    """Get list of collection names in Qdrant (for Qdrant Indexing step)."""
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


def get_embed_models(token: Optional[str] = None) -> tuple[list[str], str]:
    """Get list of embed models for step3. Returns (models, default_model)."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = requests.get(f"{API_BASE}/pipeline/embed-models", headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return (data.get("models", []), data.get("default", "qwen3-embedding:8b"))
    except Exception:
        return (["qwen3-embedding:8b", "nomic-embed-text", "mxbai-embed-large", "all-minilm"], "qwen3-embedding:8b")


def run_pipeline_step(
    step: str,
    only_folders: Optional[list[str]] = None,
    force_rerun: bool = False,
    collection_name: Optional[str] = None,
    qdrant_url: Optional[str] = None,
    embed_model: Optional[str] = None,
    token: Optional[str] = None,
) -> dict:
    """Run pipeline step; only_folders = None or [] = run all; force_rerun = rerun even if done; collection_name / qdrant_url = step4 only; embed_model = step3 only."""
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
    if step == "step3" and embed_model and embed_model.strip():
        body["embed_model"] = embed_model.strip()
    resp = requests.post(
        f"{API_BASE}/pipeline/run/{step}",
        json=body if body else None,
        headers=headers,
        timeout=3600,
    )
    resp.raise_for_status()
    return resp.json()
