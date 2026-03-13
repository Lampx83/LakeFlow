"""
Step 2 - Multi-format Processing
200_staging → 300_processed
"""

from pathlib import Path
import os
import json

from dotenv import load_dotenv
load_dotenv()

from lakeflow.runtime.config import runtime_config
from lakeflow.config import paths
from lakeflow.common.raw_finder import find_raw_file

# Import specialized processing pipelines
from lakeflow.pipelines.processing.pdf_pipeline import run_pdf_pipeline
from lakeflow.pipelines.processing.word_pipeline import run_word_pipeline
from lakeflow.pipelines.processing.excel_pipeline import run_excel_pipeline


data_base = os.getenv("LAKE_ROOT")
if not data_base:
    raise RuntimeError("LAKE_ROOT is not set.")

base_path = Path(data_base).expanduser().resolve()
runtime_config.set_data_base_path(base_path)

print(f"[BOOT] DATA_BASE_PATH_STEP2 = {base_path}")


def main():
    print("=== RUN MULTI-FORMAT PROCESSING (300_processed) ===")

    staging_root = paths.staging_path()
    raw_root = paths.raw_path()
    processed_root = paths.processed_path()

    if not staging_root.exists():
        raise RuntimeError(f"STAGING_PATH does not exist: {staging_root}")

    only_folders_env = os.getenv("PIPELINE_ONLY_FOLDERS")
    only_folders = [s.strip() for s in (only_folders_env or "").split(",") if s.strip()] or None
    force_rerun = os.getenv("PIPELINE_FORCE_RERUN") == "1"
    
    processed_count = 0

    # Find directories that have been successfully staged (support nested: 200_staging/Library/Quy/file_hash/)
    def iter_staging_entries():
        for path in staging_root.rglob("validation.json"):
            if not path.is_file():
                continue
            staging_dir = path.parent
            if staging_dir != staging_root and staging_dir.is_dir():
                yield staging_dir

    staging_dirs = list(iter_staging_entries())
    print(f"[DEBUG] Found {len(staging_dirs)} staging entries to process")

    only_folders_set = set(only_folders) if only_folders else None

    for staging_dir in staging_dirs:
        file_hash = staging_dir.name
        parent_dir = str(staging_dir.parent.relative_to(staging_root)).replace("\\", "/") if staging_dir.parent != staging_root else ""
        rel_path = f"{parent_dir}/{file_hash}" if parent_dir else file_hash

        # Folder filter logic (preserved from original code)
        if only_folders_set is not None:
            if not (rel_path in only_folders_set or 
                    any(rel_path.startswith(p + "/") for p in only_folders_set) or
                    (parent_dir and parent_dir in only_folders_set)):
                continue

        # Find original file in 100_raw (same folder structure)
        raw_file = find_raw_file(file_hash, raw_root, parent_dir=parent_dir or None)
        if raw_file is None:
            print(f"[SKIP] Raw file not found for {file_hash}")
            continue

        # Determine target directory in 300_processed (preserve folder structure)
        processed_dir = processed_root / parent_dir / file_hash if parent_dir else processed_root / file_hash
        if not force_rerun and (processed_dir / "chunks.json").exists():
            print(f"[SKIP] Already processed: {file_hash}")
            continue

        try:
            # --- ROUTE BASED ON VALIDATION.JSON ---
            with open(staging_dir / "validation.json", "r", encoding="utf-8") as f:
                validation = json.load(f)
            
            file_type = validation.get("file_type")
            print(f"[PROCESS][{file_type.upper()}] Running pipeline for: {raw_file.name}")

            if file_type == "pdf":
                run_pdf_pipeline(
                    file_hash=file_hash,
                    raw_file_path=raw_file,  # Renamed to raw_file_path for consistency
                    output_dir=processed_dir,
                    validation=validation
                )          
            elif file_type == "docx":
                run_word_pipeline(
                    file_hash=file_hash,
                    raw_file_path=raw_file,
                    output_dir=processed_dir,
                    validation=validation
                )
            elif file_type in ["xlsx", "xls"]:
                run_excel_pipeline(
                    file_hash=file_hash,
                    raw_file_path=raw_file,
                    output_dir=processed_dir,
                    validation=validation
                )
            else:
                print(f"[WARN] Unknown file type {file_type} for {file_hash}")
                continue

            processed_count += 1

        except Exception as exc:
            print(f"[ERROR] Failed processing {file_hash}: {exc}")

    print("\n" + "="*35)
    print(f"DONE. Total processed: {processed_count}")
    print("="*35)


if __name__ == "__main__":
    main()



# lampx-------------------------------------
# """
# Step 2 – Processing
# 200_staging → 300_processed
# """

# from pathlib import Path
# import os

# from dotenv import load_dotenv
# load_dotenv()

# from lakeflow.runtime.config import runtime_config
# from lakeflow.pipelines.processing.pipeline import run_processed_pipeline
# from lakeflow.config import paths
# from lakeflow.common.raw_finder import find_raw_file


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

# print(f"[BOOT] DATA_BASE_PATH2 = {base_path}")


# # ======================================================
# # MAIN
# # ======================================================

# def main():
#     print("=== RUN 300_PROCESSED PIPELINE ===")

#     staging_root = paths.staging_path()
#     raw_root = paths.raw_path()
#     processed_root = paths.processed_path()

#     print(f"[DEBUG] STAGING_PATH   = {staging_root}")
#     print(f"[DEBUG] RAW_PATH       = {raw_root}")
#     print(f"[DEBUG] PROCESSED_PATH = {processed_root}")

#     if not staging_root.exists():
#         raise RuntimeError(f"STAGING_PATH does not exist: {staging_root}")

#     only_folders_env = os.getenv("PIPELINE_ONLY_FOLDERS")
#     only_folders = [s.strip() for s in (only_folders_env or "").split(",") if s.strip()] or None
#     force_rerun = os.getenv("PIPELINE_FORCE_RERUN") == "1"
#     if only_folders:
#         print(f"[PROCESSING] Running only folders: {only_folders}")
#     if force_rerun:
#         print("[PROCESSING] Force re-run: run again even if already processed")

#     processed_count = 0

#     # 200_staging: can be <domain>/<file_hash>/ or (legacy) <file_hash>/
#     def iter_staging_entries():
#         for entry in staging_root.iterdir():
#             if not entry.is_dir():
#                 continue
#             if (entry / "validation.json").exists():
#                 yield entry  # legacy structure: staging_root/file_hash/
#             else:
#                 for sub in entry.iterdir():
#                     if sub.is_dir() and (sub / "validation.json").exists():
#                         yield sub  # new structure: staging_root/domain/file_hash/

#     staging_dirs = list(iter_staging_entries())
#     print(f"[DEBUG] Found {len(staging_dirs)} staging dirs")

#     only_folders_set = set(only_folders) if only_folders else None

#     for staging_dir in staging_dirs:
#         file_hash = staging_dir.name
#         parent_name = staging_dir.parent.name if staging_dir.parent != staging_root else None
#         rel_path = f"{parent_name}/{file_hash}" if parent_name else file_hash

#         # Filter by selected tree folder: domain, domain/file_hash, or file_hash (legacy)
#         if only_folders_set is not None:
#             if rel_path in only_folders_set:
#                 pass
#             elif any(rel_path.startswith(p + "/") for p in only_folders_set):
#                 pass  # parent folder selected → run all children
#             elif parent_name and parent_name in only_folders_set:
#                 pass
#             elif not parent_name and file_hash in only_folders_set:
#                 pass
#             else:
#                 continue

#         raw_file = find_raw_file(file_hash, raw_root)

#         if raw_file is None:
#             print(f"[SKIP] Raw file not found for {file_hash}")
#             continue

#         try:
#             run_processed_pipeline(
#                 file_hash=file_hash,
#                 raw_file_path=raw_file,
#                 staging_dir=staging_dir,
#                 processed_root=processed_root,
#                 force=force_rerun,
#                 parent_dir=parent_name or None,
#             )
#             processed_count += 1

#         except Exception as exc:
#             print(f"[ERROR] Failed processing {file_hash}: {exc}")

#     print("=================================")
#     print(f"=== DONE. Processed files: {processed_count} ===")
#     print("=================================")


# if __name__ == "__main__":
#     main()
