"""
Inbox API: upload files into 000_inbox and list by domain.

- POST /inbox/upload: multipart form (domain, file(s)) -> write to inbox_path()/domain/
  Sau khi upload thành công, tự chạy pipeline (step0→step4) cho domain đó; collection Qdrant = tên domain.
- GET /inbox/domains: list top-level subdirs of 000_inbox
- GET /inbox/list?domain=...: list files in a domain folder
"""

import json
import logging
import os
import re
import threading
import urllib.request
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from lakeflow.config import paths

logger = logging.getLogger(__name__)

router = APIRouter()

# Same as pipeline ingest allowed extensions
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".xls", ".pptx", ".txt"}
# Safe folder name: alphanumeric, underscore, hyphen only
DOMAIN_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB per file


def _inbox_root() -> Path:
    root = paths.inbox_path()
    root.mkdir(parents=True, exist_ok=True)
    return root


@router.post("/upload")
async def upload_to_inbox(
    domain: str = Form(..., description="Subfolder under 000_inbox (e.g. quy_dinh, syllabus, Regulations and Policies)"),
    path: Optional[str] = Form(None, description="Subpath under domain (e.g. thư mục con). Để trống = upload vào gốc domain."),
    files: list[UploadFile] = File(..., description="Files to upload"),
    qdrant_url: Optional[str] = Form(None, description="URL Qdrant để step4 ghi vector (trống = dùng Qdrant mặc định của Datalake). VD: http://host.docker.internal:8010 cho Research Qdrant."),
):
    """Upload one or more files into 000_inbox/<domain>/<path>/ (path optional)."""
    domain = (domain or "").strip()
    if not domain:
        raise HTTPException(status_code=400, detail="domain is required")
    root = _inbox_root()
    domain_root = _domain_path_safe(root, domain)
    if domain_root is None:
        raise HTTPException(
            status_code=400,
            detail="domain invalid (no .. or path separators)",
        )
    target_dir = _domain_subpath_safe(domain_root, path or "")
    if target_dir is None:
        raise HTTPException(status_code=400, detail="path invalid (no .. or path separators)")

    target_dir.mkdir(parents=True, exist_ok=True)

    uploaded: list[str] = []
    errors: list[str] = []

    for f in files or []:
        if not f.filename:
            errors.append("One file had no filename")
            continue
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            errors.append(f"{f.filename}: extension {ext} not allowed (allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))})")
            continue
        # Safe filename: keep original name but avoid path traversal
        safe_name = os.path.basename(f.filename)
        if ".." in safe_name or safe_name.startswith("/"):
            errors.append(f"{f.filename}: invalid filename")
            continue
        dest = target_dir / safe_name
        try:
            content = await f.read()
            if len(content) > MAX_FILE_SIZE:
                errors.append(f"{f.filename}: file too large (max {MAX_FILE_SIZE // (1024*1024)} MB)")
                continue
            dest.write_bytes(content)
            uploaded.append(safe_name)
        except Exception as e:
            errors.append(f"{f.filename}: {e!s}")

    # Tự chạy pipeline cho domain (step0→step4), collection Qdrant = tên domain; có thể ghi sang qdrant_url (VD Research Qdrant)
    if uploaded:
        _trigger_pipeline_for_domain(domain, qdrant_url=(qdrant_url or "").strip() or None)

    return {"uploaded": uploaded, "errors": errors}


def _trigger_pipeline_for_domain(domain: str, qdrant_url: Optional[str] = None) -> None:
    """Chạy pipeline (step0→step4) cho domain trong background; step4 dùng collection_name = domain, có thể ghi sang qdrant_url."""
    base_url = os.getenv("LAKEFLOW_PIPELINE_BASE_URL", "http://127.0.0.1:8011").rstrip("/")

    def _run() -> None:
        steps = ["step0", "step1", "step2", "step3", "step4"]
        for step in steps:
            body = {"only_folders": [domain]}
            if step == "step4":
                body["collection_name"] = domain
                if qdrant_url:
                    body["qdrant_url"] = qdrant_url
            data = json.dumps(body).encode("utf-8")
            req = urllib.request.Request(
                f"{base_url}/pipeline/run/{step}",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=3600) as resp:
                    result = json.loads(resp.read().decode())
                    rc = result.get("returncode", -1)
                    if rc != 0:
                        logger.warning(
                            "[inbox] Pipeline %s for domain %s returncode=%s stderr=%s",
                            step, domain, rc, result.get("stderr", "")[:500],
                        )
            except Exception as e:
                logger.exception("[inbox] Pipeline %s for domain %s failed: %s", step, domain, e)
                return

    threading.Thread(target=_run, daemon=True).start()


@router.get("/domains")
def list_domains():
    """List top-level subdirectories of 000_inbox (domain names)."""
    root = _inbox_root()
    if not root.exists():
        return {"domains": []}
    domains = [
        d.name
        for d in sorted(root.iterdir())
        if d.is_dir() and not d.name.startswith(".")
    ]
    return {"domains": domains}


def _domain_path_safe(root: Path, domain: str) -> Optional[Path]:
    """Return path to 000_inbox/<domain> if safe (no path traversal). Accept any folder name including spaces."""
    domain = (domain or "").strip()
    if not domain or ".." in domain or "/" in domain or "\\" in domain:
        return None
    target = root / domain
    try:
        target.resolve().relative_to(root.resolve())
    except (ValueError, OSError):
        return None
    return target


def _domain_subpath_safe(domain_root: Path, subpath: str) -> Optional[Path]:
    """Resolve domain_root / subpath (e.g. subpath='a/b/c') safely. No '..' or absolute segments."""
    if not subpath or not subpath.strip():
        return domain_root
    parts = [p for p in subpath.strip().replace("\\", "/").split("/") if p and p != "."]
    if any(p == ".." for p in parts):
        return None
    target = domain_root
    for p in parts:
        target = target / p
    try:
        target.resolve().relative_to(domain_root.resolve())
    except (ValueError, OSError):
        return None
    return target


@router.get("/list")
def list_files(domain: Optional[str] = None, path: Optional[str] = None):
    """
    If domain is given: list folders and files in 000_inbox/<domain>/<path>/.
    path is optional (subpath, can be multi-level e.g. 'folder1/folder2').
    If domain is omitted: same as GET /domains (list domain names).
    Returns: domain, path, folders[], files[].
    """
    root = _inbox_root()
    if not domain or not domain.strip():
        if not root.exists():
            return {"files": [], "folders": [], "domain": None, "path": ""}
        domains = [
            d.name
            for d in sorted(root.iterdir())
            if d.is_dir() and not d.name.startswith(".")
        ]
        return {"domains": domains, "files": [], "folders": []}

    domain = domain.strip()
    domain_root = _domain_path_safe(root, domain)
    if domain_root is None:
        raise HTTPException(status_code=400, detail="Invalid domain")
    target_dir = _domain_subpath_safe(domain_root, path or "")
    if target_dir is None:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not target_dir.exists() or not target_dir.is_dir():
        return {"domain": domain, "path": path or "", "folders": [], "files": []}

    folders: list[str] = []
    files_list: list[dict] = []
    for p in sorted(target_dir.iterdir()):
        if p.name.startswith("."):
            continue
        if p.is_dir():
            folders.append(p.name)
        else:
            stat = p.stat()
            files_list.append({
                "name": p.name,
                "size": stat.st_size,
                "mtime": stat.st_mtime,
            })
    rel_path = path.strip() if path else ""
    return {"domain": domain, "path": rel_path, "folders": folders, "files": files_list}
