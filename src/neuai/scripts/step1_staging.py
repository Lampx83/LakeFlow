# src/neuai/scripts/run_pdf_staging.py

from pathlib import Path

from neuai.processing.staging.pipeline import run_pdf_staging
from neuai.config.paths import RAW_PATH, STAGING_PATH


def extract_file_hash(pdf_path: Path) -> str:
    """
    File trong 100_raw có dạng:
        <file_hash>.pdf
    """
    return pdf_path.stem


def already_staged(file_hash: str) -> bool:
    """
    Kiểm tra đã có kết quả validation chưa
    """
    validation_file = STAGING_PATH / file_hash / "validation.json"
    return validation_file.exists()


def main():
    print("=== RUN PDF STAGING (200_staging) ===")

    if not RAW_PATH.exists():
        raise RuntimeError(f"RAW_PATH does not exist: {RAW_PATH}")

    processed = 0
    skipped = 0
    failed = 0

    for pdf_path in RAW_PATH.rglob("*.pdf"):
        file_hash = extract_file_hash(pdf_path)

        if already_staged(file_hash):
            print(f"[STAGING][SKIP] Already staged: {file_hash}")
            skipped += 1
            continue

        print(f"[STAGING][PDF] Processing: {pdf_path.name}")

        try:
            run_pdf_staging(
                file_hash=file_hash,
                raw_pdf_path=pdf_path,
                staging_root=STAGING_PATH,
            )
            processed += 1

        except Exception as exc:
            failed += 1
            print(
                f"[STAGING][ERROR] Failed processing {pdf_path.name}\n"
                f"                Reason: {exc}"
            )
            # không raise để tiếp tục file khác

    print("=================================")
    print(f"PDF processed : {processed}")
    print(f"PDF skipped   : {skipped}")
    print(f"PDF failed    : {failed}")
    print("=================================")


if __name__ == "__main__":
    main()
