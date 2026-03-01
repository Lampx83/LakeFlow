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

from lakeflow.common.nas_io import nas_safe_exists, nas_safe_is_dir, nas_safe_listdir, nas_safe_load_npy
from lakeflow.runtime.config import runtime_config
from lakeflow.config import paths
from lakeflow.vectorstore.qdrant_ingest import (
    ingest_file_embeddings,
    ensure_collection,
)


data_base = os.getenv("LAKE_ROOT")
if not data_base:
    raise RuntimeError(
        "LAKE_ROOT is not set. "
        "Example: export LAKE_ROOT=/path/to/data_lake"
    )

base_path = Path(data_base).expanduser().resolve()
runtime_config.set_data_base_path(base_path)

print(f"[BOOT] DATA_BASE_PATH3 = {base_path}")


QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))


def main():
    print("=== RUN QDRANT INGEST (400 -> Qdrant) ===")

    embeddings_root = paths.embeddings_path()
    processed_root = paths.processed_path()

    print(f"[DEBUG] EMBEDDINGS_PATH = {embeddings_root}")
    print(f"[DEBUG] PROCESSED_PATH  = {processed_root}")

    if not nas_safe_exists(embeddings_root):
        raise RuntimeError(
            f"EMBEDDINGS_PATH does not exist: {embeddings_root}"
        )

    if not nas_safe_exists(processed_root):
        raise RuntimeError(
            f"PROCESSED_PATH does not exist: {processed_root}"
        )

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
        print(f"[QDRANT] Running only folders: {only_folders}")
    if collection_name:
        print(f"[QDRANT] Collection: {collection_name}")

    ingested = skipped = failed = 0

    # 400_embeddings: <domain>/<file_hash>/ or (legacy) <file_hash>/
    # Use nas_safe_* to avoid Errno 35 (resource deadlock) on NAS/shared volumes
    def iter_embeddings_entries():
        for entry in nas_safe_listdir(embeddings_root):
            if not nas_safe_is_dir(entry) or entry.name.startswith("."):
                continue
            if nas_safe_exists(entry / "embedding.npy"):
                yield entry  # legacy: embeddings_root/file_hash/
            else:
                for sub in nas_safe_listdir(entry):
                    if nas_safe_is_dir(sub) and nas_safe_exists(sub / "embedding.npy"):
                        yield sub  # new: embeddings_root/domain/file_hash/

    emb_dirs = list(iter_embeddings_entries())
    print(f"[DEBUG] Found {len(emb_dirs)} embedding dirs")

    only_folders_set = set(only_folders) if only_folders else None

    for emb_dir in emb_dirs:
        file_hash = emb_dir.name
        parent_name = emb_dir.parent.name if emb_dir.parent != embeddings_root else None
        rel_path = f"{parent_name}/{file_hash}" if parent_name else file_hash

        # Filter by selected tree folder: domain, domain/file_hash, or file_hash (legacy)
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

        if not nas_safe_exists(embeddings_file):
            print(f"[QDRANT][SKIP] No embedding.npy for {file_hash}")
            skipped += 1
            continue

        try:
            vectors = nas_safe_load_npy(embeddings_file)
            if vectors.ndim != 2:
                raise RuntimeError(
                    f"Invalid embedding shape for {file_hash}"
                )

            ensure_collection(
                client=client,
                vector_dim=vectors.shape[1],
                collection_name=collection_name,
            )

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

    print("\n=================================")
    print("QDRANT INGEST SUMMARY")
    print(f"Ingested : {ingested}")
    print(f"Skipped  : {skipped}")
    print(f"Failed   : {failed}")
    print("=================================")


if __name__ == "__main__":
    main()
