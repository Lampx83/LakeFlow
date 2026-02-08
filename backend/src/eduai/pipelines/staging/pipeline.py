from pathlib import Path
from typing import Optional

from eduai.common.jsonio import write_json
from eduai.pipelines.staging.pdf_analyzer import analyze_pdf


def run_pdf_staging(
    file_hash: str,
    raw_pdf_path: Path,
    staging_root: Path,
    parent_dir: Optional[str] = None,
) -> None:
    """
    Chạy pipeline staging cho PDF (200_staging).

    parent_dir: thư mục cha (domain) — output sẽ là 200_staging/<parent_dir>/<file_hash>/
    Nếu không truyền: 200_staging/<file_hash>/ (giữ tương thích).

    Sinh:
      - pdf_profile.json
      - validation.json
      - (tuỳ chọn) text_sample.txt
    """

    if parent_dir:
        staging_dir = staging_root / parent_dir / file_hash
    else:
        staging_dir = staging_root / file_hash
    staging_dir.mkdir(parents=True, exist_ok=True)

    # ---------- 1. Analyze PDF ----------
    profile = analyze_pdf(raw_pdf_path)

    write_json(
        staging_dir / "pdf_profile.json",
        profile,
    )

    # ---------- 2. Build validation ----------
    validation = {
        "file_type": "pdf",
        "requires_ocr": profile.get("is_scanned", False),
        "has_tables": profile.get("has_tables", False),
        "recommended_pipeline": ["pdf_text_extract"],
    }

    write_json(
        staging_dir / "validation.json",
        validation,
    )
