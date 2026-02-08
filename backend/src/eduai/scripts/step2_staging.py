"""
Step 2 – Processing
200_staging → 300_processed
"""

from pathlib import Path
import os

from dotenv import load_dotenv
load_dotenv()

from eduai.runtime.config import runtime_config
from eduai.pipelines.processing.pipeline import run_processed_pipeline
from eduai.config import paths
from eduai.common.raw_finder import find_raw_file


# ======================================================
# BOOTSTRAP RUNTIME CONFIG (BẮT BUỘC)
# ======================================================

data_base = os.getenv("EDUAI_DATA_BASE_PATH")
if not data_base:
    raise RuntimeError(
        "EDUAI_DATA_BASE_PATH is not set. "
        "Example: export EDUAI_DATA_BASE_PATH=/path/to/data_lake"
    )

base_path = Path(data_base).expanduser().resolve()
runtime_config.set_data_base_path(base_path)

print(f"[BOOT] DATA_BASE_PATH2 = {base_path}")


# ======================================================
# MAIN
# ======================================================

def main():
    print("=== RUN 300_PROCESSED PIPELINE ===")

    staging_root = paths.staging_path()
    raw_root = paths.raw_path()
    processed_root = paths.processed_path()

    print(f"[DEBUG] STAGING_PATH   = {staging_root}")
    print(f"[DEBUG] RAW_PATH       = {raw_root}")
    print(f"[DEBUG] PROCESSED_PATH = {processed_root}")

    if not staging_root.exists():
        raise RuntimeError(f"STAGING_PATH does not exist: {staging_root}")

    only_folders_env = os.getenv("PIPELINE_ONLY_FOLDERS")
    only_folders = [s.strip() for s in (only_folders_env or "").split(",") if s.strip()] or None
    force_rerun = os.getenv("PIPELINE_FORCE_RERUN") == "1"
    if only_folders:
        print(f"[PROCESSING] Chỉ chạy các thư mục: {only_folders}")
    if force_rerun:
        print("[PROCESSING] Force re-run: chạy lại kể cả đã xử lý")

    processed_count = 0

    # 200_staging: có thể là <domain>/<file_hash>/ hoặc (cũ) <file_hash>/
    def iter_staging_entries():
        for entry in staging_root.iterdir():
            if not entry.is_dir():
                continue
            if (entry / "validation.json").exists():
                yield entry  # cấu trúc cũ: staging_root/file_hash/
            else:
                for sub in entry.iterdir():
                    if sub.is_dir() and (sub / "validation.json").exists():
                        yield sub  # cấu trúc mới: staging_root/domain/file_hash/

    staging_dirs = list(iter_staging_entries())
    print(f"[DEBUG] Found {len(staging_dirs)} staging dirs")

    only_folders_set = set(only_folders) if only_folders else None

    for staging_dir in staging_dirs:
        file_hash = staging_dir.name
        parent_name = staging_dir.parent.name if staging_dir.parent != staging_root else None
        rel_path = f"{parent_name}/{file_hash}" if parent_name else file_hash

        # Lọc theo thư mục đã chọn trên cây: domain, domain/file_hash, hoặc file_hash (cấu trúc cũ)
        if only_folders_set is not None:
            if rel_path in only_folders_set:
                pass
            elif any(rel_path.startswith(p + "/") for p in only_folders_set):
                pass  # chọn thư mục cha → chạy cả con
            elif parent_name and parent_name in only_folders_set:
                pass
            elif not parent_name and file_hash in only_folders_set:
                pass
            else:
                continue

        raw_file = find_raw_file(file_hash, raw_root)

        if raw_file is None:
            print(f"[SKIP] Raw file not found for {file_hash}")
            continue

        try:
            run_processed_pipeline(
                file_hash=file_hash,
                raw_file_path=raw_file,
                staging_dir=staging_dir,
                processed_root=processed_root,
                force=force_rerun,
                parent_dir=parent_name or None,
            )
            processed_count += 1

        except Exception as exc:
            print(f"[ERROR] Failed processing {file_hash}: {exc}")

    print("=================================")
    print(f"=== DONE. Processed files: {processed_count} ===")
    print("=================================")


if __name__ == "__main__":
    main()
