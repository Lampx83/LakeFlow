"""
Step 1 – Multi-format Staging
100_raw → 200_staging
Supports: PDF, DOCX, XLSX, XLS
"""

from pathlib import Path
import os
from typing import List

from dotenv import load_dotenv
load_dotenv()

from lakeflow.runtime.config import runtime_config
# Import staging functions from new pipeline
from lakeflow.pipelines.staging.pipeline import (
    run_pdf_staging, 
    run_word_staging, 
    run_excel_staging
)
from lakeflow.pipelines.staging.pdf_analyzer import StagingError
from lakeflow.config import paths


data_base = os.getenv("LAKE_ROOT")
if not data_base:
    raise RuntimeError("LAKE_ROOT is not set.")

base_path = Path(data_base).expanduser().resolve()
runtime_config.set_data_base_path(base_path)

print(f"[BOOT] DATA_BASE_PATH = {base_path}")


def extract_file_hash(file_path: Path) -> str:
    """Hash is the file name (stem) because Step 0 renamed files to SHA256."""
    return file_path.stem


def _parent_dir_from_raw(file_path: Path, raw_root: Path) -> str:
    """Full path of file's parent relative to 100_raw (preserves nested folders, e.g. 'Library/Quy định hướng dẫn')."""
    try:
        rel = file_path.relative_to(raw_root)
        return str(rel.parent).replace("\\", "/")
    except ValueError:
        return ""


def already_staged(file_hash: str, parent_dir: str = "") -> bool:
    """Check whether file already has validation.json in 200_staging (parent_dir can contain '/')."""
    root = paths.staging_path()
    # parent_dir can be "Library/Quy định hướng dẫn"
    check_path = root / parent_dir / file_hash / "validation.json" if parent_dir else root / file_hash / "validation.json"
    return check_path.exists()


def main():
    print("=== RUN MULTI-FORMAT STAGING (200_staging) ===")

    raw_root = paths.raw_path()
    if not raw_root.exists():
        raise RuntimeError(f"RAW_PATH does not exist: {raw_root}")

    # Configure folder filter and overwrite
    only_folders_env = os.getenv("PIPELINE_ONLY_FOLDERS")
    only_path_prefixes = [s.strip().rstrip("/") for s in (only_folders_env or "").split(",") if s.strip()] or None
    force_rerun = os.getenv("PIPELINE_FORCE_RERUN") == "1"

    processed = skipped = failed = 0

    # Important: extend supported file formats
    allowed_extensions = {".pdf", ".docx", ".xlsx", ".xls"}
    
    all_files = [
        p for p in raw_root.rglob("*") 
        if p.is_file() and p.suffix.lower() in allowed_extensions
    ]
    
    print(f"[DEBUG] Found {len(all_files)} files to analyze")

    for file_path in all_files:
        # Filter by folder if PIPELINE_ONLY_FOLDERS is set
        if only_path_prefixes:
            try:
                rel_str = str(file_path.relative_to(raw_root)).replace("\\", "/")
                if not any(rel_str == p or rel_str.startswith(p + "/") for p in only_path_prefixes):
                    continue
            except ValueError:
                continue

        file_hash = extract_file_hash(file_path)
        parent_dir = _parent_dir_from_raw(file_path, raw_root)
        ext = file_path.suffix.lower()

        # Check for duplicates
        if not force_rerun and already_staged(file_hash, parent_dir):
            print(f"[STAGING][SKIP] Already staged: {file_hash} ({ext})")
            skipped += 1
            continue

        print(f"[STAGING][{ext.upper()}] Processing: {file_path.name}")

        try:
            # Route processing by file format
            if ext == ".pdf":
                run_pdf_staging(
                    file_hash=file_hash,
                    raw_pdf_path=file_path,
                    staging_root=paths.staging_path(),
                    parent_dir=parent_dir or None,
                )
            elif ext == ".docx":
                run_word_staging(
                    file_hash=file_hash,
                    raw_docx_path=file_path,
                    staging_root=paths.staging_path(),
                    parent_dir=parent_dir or None,
                )
            elif ext in {".xlsx", ".xls"}:
                run_excel_staging(
                    file_hash=file_hash,
                    raw_excel_path=file_path,
                    staging_root=paths.staging_path(),
                    parent_dir=parent_dir or None,
                )
            
            processed += 1

        except StagingError as exc:
            failed += 1
            print(f"[STAGING][ERROR] {file_path.name} -> {exc}")
        except Exception as exc:
            failed += 1
            print(f"[STAGING][CRITICAL] {file_path.name} -> {type(exc).__name__}: {exc}")

    print("\n" + "="*35)
    print(f"Total processed : {processed}")
    print(f"Total skipped   : {skipped}")
    print(f"Total failed    : {failed}")
    print("="*35)


if __name__ == "__main__":
    main()

    
# lampx===================================================
# """
# Step 1 – PDF Staging
# 100_raw → 200_staging
# """

# from pathlib import Path
# import os

# from dotenv import load_dotenv
# load_dotenv()

# from lakeflow.runtime.config import runtime_config
# from lakeflow.pipelines.staging.pipeline import run_pdf_staging
# from lakeflow.pipelines.staging.pdf_analyzer import StagingError
# from lakeflow.config import paths


# # ======================================================
# # BOOTSTRAP RUNTIME CONFIG (REQUIRED)
# # ======================================================

# data_base = os.getenv("LAKE_ROOT")
# if not data_base:
#     raise RuntimeError(
#         "LAKE_ROOT is not set. "
#         "Example: export LAKE_ROOT=/path/to/data_lake"
#     )

# base_path = Path(data_base).expanduser().resolve()
# runtime_config.set_data_base_path(base_path)

# print(f"[BOOT] DATA_BASE_PATH1 = {base_path}")


# # ======================================================
# # HELPERS
# # ======================================================

# def extract_file_hash(pdf_path: Path) -> str:
#     return pdf_path.stem


# def _parent_dir_from_raw(pdf_path: Path, raw_root: Path) -> str:
#     """Parent directory in 100_raw (domain)."""
#     try:
#         rel = pdf_path.relative_to(raw_root)
#         return rel.parts[0] if rel.parts else ""
#     except ValueError:
#         return ""


# def already_staged(file_hash: str, parent_dir: str = "") -> bool:
#     """Check if already staged (200_staging/<parent_dir>/<file_hash>/validation.json)."""
#     root = paths.staging_path()
#     if parent_dir:
#         return (root / parent_dir / file_hash / "validation.json").exists()
#     return (root / file_hash / "validation.json").exists()


# # ======================================================
# # MAIN
# # ======================================================

# def main():
#     print("=== RUN PDF STAGING (200_staging) ===")

#     raw_root = paths.raw_path()
#     print(f"[DEBUG] RAW_PATH = {raw_root}")

#     if not raw_root.exists():
#         raise RuntimeError(f"RAW_PATH does not exist: {raw_root}")

#     only_folders_env = os.getenv("PIPELINE_ONLY_FOLDERS")
#     only_path_prefixes = [s.strip().rstrip("/") for s in (only_folders_env or "").split(",") if s.strip()] or None
#     force_rerun = os.getenv("PIPELINE_FORCE_RERUN") == "1"
#     if only_path_prefixes:
#         print(f"[STAGING] Running only folders: {only_path_prefixes}")
#     if force_rerun:
#         print("[STAGING] Force re-run: run again even if already staged")

#     processed = skipped = failed = 0

#     # Find both PDF and DOCX files
#     allowed_extensions = {".pdf", ".docx"}
#     all_files = [
#         p for p in raw_root.rglob("*") 
#         if p.is_file() and p.suffix.lower() in allowed_extensions
#     ]
#     print(f"[DEBUG] Found {len(all_files)} files (PDF/DOCX)")

#     # pdf_files = [p for p in raw_root.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"]
#     # print(f"[DEBUG] Found {len(pdf_files)} PDF files")

#     for pdf_path in pdf_files:
#         if only_path_prefixes:
#             try:
#                 rel_str = str(pdf_path.relative_to(raw_root)).replace("\\", "/")
#                 if not any(rel_str == p or rel_str.startswith(p + "/") for p in only_path_prefixes):
#                     continue
#             except ValueError:
#                 continue
#         file_hash = extract_file_hash(pdf_path)
#         parent_dir = _parent_dir_from_raw(pdf_path, raw_root)

#         if not force_rerun and already_staged(file_hash, parent_dir):
#             print(f"[STAGING][SKIP] Already staged: {file_hash}")
#             skipped += 1
#             continue

#         print(f"[STAGING][PDF] Processing: {pdf_path}")

#         try:
#             run_pdf_staging(
#                 file_hash=file_hash,
#                 raw_pdf_path=pdf_path,
#                 staging_root=paths.staging_path(),
#                 parent_dir=parent_dir or None,
#             )
#             processed += 1

#         except StagingError as exc:
#             failed += 1
#             print(f"[STAGING][ERROR] {pdf_path.name}")
#             print(f"                Reason: {exc}")
#         except Exception as exc:
#             failed += 1
#             print(f"[STAGING][ERROR] {pdf_path.name}")
#             print(f"                Reason: {type(exc).__name__}: {exc}")

#     print("=================================")
#     print(f"PDF processed : {processed}")
#     print(f"PDF skipped   : {skipped}")
#     print(f"PDF failed    : {failed}")
#     print("=================================")


# if __name__ == "__main__":
#     main()
