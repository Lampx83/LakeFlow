"""
Step 3 – Embeddings
300_processed → 400_embeddings
"""

from pathlib import Path
import os

from dotenv import load_dotenv
load_dotenv()

from eduai.runtime.config import runtime_config
from eduai.pipelines.embedding.pipeline import run_embedding_pipeline
from eduai.config import paths


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

print(f"[BOOT] DATA_BASE_PATH3 = {base_path}")


# ======================================================
# MAIN
# ======================================================

def main():
    print("=== RUN 400_EMBEDDINGS PIPELINE ===")

    processed_root = paths.processed_path()
    embeddings_root = paths.embeddings_path()

    print(f"[DEBUG] PROCESSED_PATH  = {processed_root}")
    print(f"[DEBUG] EMBEDDINGS_PATH = {embeddings_root}")

    if not processed_root.exists():
        raise RuntimeError(f"PROCESSED_PATH does not exist: {processed_root}")

    only_folders_env = os.getenv("PIPELINE_ONLY_FOLDERS")
    only_folders = [s.strip() for s in (only_folders_env or "").split(",") if s.strip()] or None
    force_rerun = os.getenv("PIPELINE_FORCE_RERUN") == "1"
    if only_folders:
        print(f"[EMBEDDING] Chỉ chạy các thư mục: {only_folders}")
    if force_rerun:
        print("[EMBEDDING] Force re-run: chạy lại kể cả đã embed")

    embedded = skipped = failed = 0

    # 300_processed: <domain>/<file_hash>/ hoặc (cũ) <file_hash>/
    def iter_processed_entries():
        for entry in processed_root.iterdir():
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            if (entry / "chunks.json").exists():
                yield entry  # cấu trúc cũ: processed_root/file_hash/
            else:
                for sub in entry.iterdir():
                    if sub.is_dir() and (sub / "chunks.json").exists():
                        yield sub  # cấu trúc mới: processed_root/domain/file_hash/

    processed_dirs = list(iter_processed_entries())
    print(f"[DEBUG] Found {len(processed_dirs)} processed dirs")

    only_folders_set = set(only_folders) if only_folders else None

    for processed_dir in processed_dirs:
        file_hash = processed_dir.name
        parent_name = processed_dir.parent.name if processed_dir.parent != processed_root else None
        rel_path = f"{parent_name}/{file_hash}" if parent_name else file_hash

        # Lọc theo thư mục đã chọn trên cây: domain, domain/file_hash, hoặc file_hash (cấu trúc cũ)
        if only_folders_set is not None:
            if rel_path in only_folders_set:
                pass
            elif any(rel_path.startswith(p + "/") for p in only_folders_set):
                pass
            elif parent_name and parent_name in only_folders_set:
                pass
            elif not parent_name and file_hash in only_folders_set:
                pass
            else:
                continue

        print(f"[400] Processing: {file_hash}")

        try:
            result = run_embedding_pipeline(
                file_hash=file_hash,
                processed_dir=processed_dir,
                embeddings_root=embeddings_root,
                force=force_rerun,
                parent_dir=parent_name or None,
            )

            if result == "SKIPPED":
                skipped += 1
                print(f"[400][SKIP] Already embedded: {file_hash}")
            else:
                embedded += 1
                print(f"[400][OK] Embedded: {file_hash}")

        except Exception as exc:
            failed += 1
            print(f"[400][ERROR] {file_hash}: {exc}")

    print("=================================")
    print(f"Embedded files : {embedded}")
    print(f"Skipped        : {skipped}")
    print(f"Failed         : {failed}")
    print("=================================")


if __name__ == "__main__":
    main()
