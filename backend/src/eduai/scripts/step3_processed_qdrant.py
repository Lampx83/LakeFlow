"""
Step 4 – Qdrant Ingest
400_embeddings → Qdrant

SOURCE OF TRUTH:
- Vectors + meta : 400_embeddings
- Text chunks    : 300_processed
"""

from pathlib import Path
import os

from dotenv import load_dotenv
load_dotenv()

import numpy as np
from qdrant_client import QdrantClient

from eduai.common.nas_io import nas_safe_load_npy
from eduai.runtime.config import runtime_config
from eduai.config import paths
from eduai.vectorstore.qdrant_ingest import (
    ingest_file_embeddings,
    ensure_collection,
)


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
# QDRANT CONFIG
# ======================================================

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))


# ======================================================
# MAIN
# ======================================================

def main():
    print("=== RUN QDRANT INGEST (400 → Qdrant) ===")

    embeddings_root = paths.embeddings_path()
    processed_root = paths.processed_path()

    print(f"[DEBUG] EMBEDDINGS_PATH = {embeddings_root}")
    print(f"[DEBUG] PROCESSED_PATH  = {processed_root}")

    if not embeddings_root.exists():
        raise RuntimeError(
            f"EMBEDDINGS_PATH does not exist: {embeddings_root}"
        )

    if not processed_root.exists():
        raise RuntimeError(
            f"PROCESSED_PATH does not exist: {processed_root}"
        )

    # -------------------------
    # Connect to Qdrant
    # -------------------------
    try:
        client = QdrantClient(
            host=QDRANT_HOST,
            port=QDRANT_PORT,
        )
        client.get_collections()  # ping
    except Exception as exc:
        raise RuntimeError(
            f"Cannot connect to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}"
        ) from exc

    only_folders_env = os.getenv("PIPELINE_ONLY_FOLDERS")
    only_folders = [s.strip() for s in (only_folders_env or "").split(",") if s.strip()] or None
    collection_name = (os.getenv("PIPELINE_QDRANT_COLLECTION") or "").strip() or None
    if only_folders:
        print(f"[QDRANT] Chỉ chạy các thư mục: {only_folders}")
    if collection_name:
        print(f"[QDRANT] Collection: {collection_name}")

    ingested = skipped = failed = 0

    # 400_embeddings: <domain>/<file_hash>/ hoặc (cũ) <file_hash>/
    def iter_embeddings_entries():
        for entry in embeddings_root.iterdir():
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            if (entry / "embedding.npy").exists():
                yield entry  # cấu trúc cũ: embeddings_root/file_hash/
            else:
                for sub in entry.iterdir():
                    if sub.is_dir() and (sub / "embedding.npy").exists():
                        yield sub  # cấu trúc mới: embeddings_root/domain/file_hash/

    emb_dirs = list(iter_embeddings_entries())
    print(f"[DEBUG] Found {len(emb_dirs)} embedding dirs")

    only_folders_set = set(only_folders) if only_folders else None

    # -------------------------
    # Iterate over embeddings
    # -------------------------
    for emb_dir in emb_dirs:
        file_hash = emb_dir.name
        parent_name = emb_dir.parent.name if emb_dir.parent != embeddings_root else None
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

        embeddings_file = emb_dir / "embedding.npy"

        print(f"\n[QDRANT] Processing {file_hash}")

        # ---------- Skip: no embedding ----------
        if not embeddings_file.exists():
            print(f"[QDRANT][SKIP] No embedding.npy for {file_hash}")
            skipped += 1
            continue

        try:
            # ---------- Load vectors (đọc từ NAS với retry) ----------
            vectors = nas_safe_load_npy(embeddings_file)
            if vectors.ndim != 2:
                raise RuntimeError(
                    f"Invalid embedding shape for {file_hash}"
                )

            # ---------- Ensure collection ----------
            ensure_collection(
                client=client,
                vector_dim=vectors.shape[1],
                collection_name=collection_name,
            )

            # ---------- Ingest (truyền parent_name để tránh iterdir trên NAS) ----------
            count = ingest_file_embeddings(
                client=client,
                file_hash=file_hash,
                embeddings_dir=emb_dir,
                processed_root=processed_root,
                collection_name=collection_name,
                parent_dir=parent_name,
            )

            print(
                f"[QDRANT][OK] {file_hash}: "
                f"{count} vectors ingested"
            )
            ingested += 1

        except Exception as exc:
            failed += 1
            print(
                f"[QDRANT][FAIL] {file_hash}: {exc}"
            )

    # -------------------------
    # Summary
    # -------------------------
    print("\n=================================")
    print("QDRANT INGEST SUMMARY")
    print(f"Ingested : {ingested}")
    print(f"Skipped  : {skipped}")
    print(f"Failed   : {failed}")
    print("=================================")


if __name__ == "__main__":
    main()
