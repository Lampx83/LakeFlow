from pathlib import Path
import numpy as np
from qdrant_client import QdrantClient

from eduai.config.paths import EMBEDDINGS_PATH
from eduai.vectorstore.qdrant_ingest import (
    ingest_file_embeddings,
    ensure_collection,
)


QDRANT_HOST = "localhost"
QDRANT_PORT = 6333


def main():
    print("=== RUN QDRANT INGEST ===")

    # -------------------------
    # Connect to Qdrant
    # -------------------------
    try:
        client = QdrantClient(
            host=QDRANT_HOST,
            port=QDRANT_PORT,
        )
        # ping nhẹ
        client.get_collections()
    except Exception as exc:
        raise RuntimeError(
            f"Cannot connect to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}"
        ) from exc

    ingested = 0
    skipped = 0
    failed = 0

    # -------------------------
    # Iterate over embeddings
    # -------------------------
    for emb_dir in EMBEDDINGS_PATH.iterdir():
        if not emb_dir.is_dir():
            continue

        file_hash = emb_dir.name
        embeddings_file = emb_dir / "embeddings.npy"

        print(f"[QDRANT] Processing {file_hash}")

        # ---------- Skip: no embeddings ----------
        if not embeddings_file.exists():
            print(f"[QDRANT][SKIP] No embeddings.npy for {file_hash}")
            skipped += 1
            continue

        try:
            # ---------- Load vectors ----------
            vectors = np.load(embeddings_file)
            if vectors.ndim != 2:
                raise RuntimeError("Invalid embeddings shape")

            # ---------- Ensure collection ----------
            ensure_collection(
                client=client,
                vector_dim=vectors.shape[1],
            )

            # ---------- Ingest ----------
            count = ingest_file_embeddings(
                client=client,
                file_hash=file_hash,
                embeddings_dir=emb_dir,
            )

            print(f"[QDRANT][OK] {file_hash}: {count} vectors ingested")
            ingested += 1

        except Exception as exc:
            print(f"[QDRANT][FAIL] {file_hash}: {exc}")
            failed += 1

    # -------------------------
    # Summary
    # -------------------------
    print("=================================")
    print(f"Ingested : {ingested}")
    print(f"Skipped  : {skipped}")
    print(f"Failed   : {failed}")
    print("=================================")


if __name__ == "__main__":
    main()
