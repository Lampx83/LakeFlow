from eduai.processing.processed.pipeline import run_processed_pipeline
from eduai.config.paths import RAW_PATH, STAGING_PATH, PROCESSED_PATH
from eduai.common.raw_finder import find_raw_file


def main():
    print("=== RUN 300_PROCESSED PIPELINE ===")

    processed_count = 0

    for staging_dir in STAGING_PATH.iterdir():
        if not staging_dir.is_dir():
            continue

        file_hash = staging_dir.name
        raw_file = find_raw_file(file_hash, RAW_PATH)

        if raw_file is None:
            print(f"[SKIP] Raw file not found for {file_hash}")
            continue

        try:
            run_processed_pipeline(
                file_hash=file_hash,
                raw_file_path=raw_file,
                staging_dir=staging_dir,
                processed_root=PROCESSED_PATH,
                force=True
            )
            processed_count += 1

        except Exception as exc:
            print(f"[ERROR] Failed processing {file_hash}: {exc}")

    print(f"=== DONE. Processed files: {processed_count} ===")


if __name__ == "__main__":
    main()
