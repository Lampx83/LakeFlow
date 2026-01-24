# src/eduai/scripts/run_embeddings.py

from eduai.processing.embeddings.pipeline import run_embedding_pipeline
from eduai.config.paths import PROCESSED_PATH, EMBEDDINGS_PATH


def main():
    print("=== RUN 400_EMBEDDINGS PIPELINE ===")

    embedded = 0
    skipped = 0
    failed = 0

    for processed_dir in PROCESSED_PATH.iterdir():
        if not processed_dir.is_dir():
            continue

        file_hash = processed_dir.name
        print(f"[400] Processing: {file_hash}")

        try:
            result = run_embedding_pipeline(
                file_hash=file_hash,
                processed_dir=processed_dir,
                embeddings_root=EMBEDDINGS_PATH,
                force=False,
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
