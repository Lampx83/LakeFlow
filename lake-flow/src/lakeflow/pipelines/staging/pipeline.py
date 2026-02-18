from pathlib import Path
from typing import Optional

from lakeflow.common.jsonio import write_json
from lakeflow.pipelines.staging.pdf_analyzer import StagingError, analyze_pdf


def _write_staging_error(staging_dir: Path, reason: str) -> None:
    """Ghi lý do lỗi vào staging_error.txt để UI/người dùng xem sau."""
    try:
        staging_dir.mkdir(parents=True, exist_ok=True)
        (staging_dir / "staging_error.txt").write_text(reason, encoding="utf-8")
    except Exception:
        pass


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

    try:
        staging_dir.mkdir(parents=True, exist_ok=True)

        # ---------- 1. Analyze PDF ----------
        try:
            profile = analyze_pdf(raw_pdf_path)
        except StagingError as e:
            _write_staging_error(staging_dir, str(e))
            raise
        except Exception as e:
            reason = f"Phân tích PDF thất bại: {e}"
            _write_staging_error(staging_dir, reason)
            raise StagingError(reason) from e

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

        try:
            write_json(
                staging_dir / "validation.json",
                validation,
            )
        except Exception as e:
            reason = f"Ghi validation.json thất bại: {e}"
            _write_staging_error(staging_dir, reason)
            raise StagingError(reason) from e

    except StagingError:
        raise
    except OSError as e:
        reason = f"Lỗi ghi thư mục/file (quyền truy cập hoặc ổ đĩa): {e}"
        _write_staging_error(staging_dir, reason)
        raise StagingError(reason) from e
