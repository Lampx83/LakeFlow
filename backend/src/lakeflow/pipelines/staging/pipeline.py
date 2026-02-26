from pathlib import Path
from typing import Optional

from lakeflow.common.jsonio import write_json
from lakeflow.pipelines.staging.pdf_analyzer import StagingError, analyze_pdf
from lakeflow.pipelines.staging.word_analyzer import analyze_word
from lakeflow.pipelines.staging.excel_analyzer import analyze_excel


def _write_staging_error(staging_dir: Path, reason: str) -> None:
    """Ghi lý do lỗi vào staging_error.txt để UI/người dùng xem sau."""
    try:
        staging_dir.mkdir(parents=True, exist_ok=True)
        (staging_dir / "staging_error.txt").write_text(reason, encoding="utf-8")
    except Exception:
        pass


def _prepare_staging_dir(staging_root: Path, file_hash: str, parent_dir: Optional[str]) -> Path:
    """Khởi tạo và trả về đường dẫn thư mục staging."""
    if parent_dir:
        staging_dir = staging_root / parent_dir / file_hash
    else:
        staging_dir = staging_root / file_hash
    staging_dir.mkdir(parents=True, exist_ok=True)
    return staging_dir


# ======================================================
# PDF STAGING
# ======================================================
def run_pdf_staging(
    file_hash: str,
    raw_pdf_path: Path,
    staging_root: Path,
    parent_dir: Optional[str] = None,
) -> None:
    staging_dir = _prepare_staging_dir(staging_root, file_hash, parent_dir)

    try:
        try:
            profile = analyze_pdf(raw_pdf_path)
        except StagingError as e:
            _write_staging_error(staging_dir, str(e))
            raise
        except Exception as e:
            reason = f"Phân tích PDF thất bại: {e}"
            _write_staging_error(staging_dir, reason)
            raise StagingError(reason) from e

        write_json(staging_dir / "pdf_profile.json", profile)

        validation = {
            "file_type": "pdf",
            "requires_ocr": profile.get("is_scanned_pdf", False),
            "has_tables": profile.get("has_images", False), # Tùy chỉnh theo logic detect table của bạn
            "recommended_pipeline": ["pdf_text_extract"],
        }
        write_json(staging_dir / "validation.json", validation)

    except (StagingError, OSError) as e:
        _write_staging_error(staging_dir, str(e))
        raise


# ======================================================
# WORD STAGING
# ======================================================
def run_word_staging(
    file_hash: str,
    raw_docx_path: Path,
    staging_root: Path,
    parent_dir: Optional[str] = None,
) -> None:
    staging_dir = _prepare_staging_dir(staging_root, file_hash, parent_dir)

    try:
        try:
            profile = analyze_word(raw_docx_path)
        except Exception as e:
            reason = f"Phân tích Word thất bại: {e}"
            _write_staging_error(staging_dir, reason)
            raise StagingError(reason) from e

        write_json(staging_dir / "word_profile.json", profile)

        validation = {
            "file_type": "docx",
            "requires_ocr": False,
            "has_tables": profile.get("table_count", 0) > 0,
            "recommended_pipeline": ["docx_text_extract"],
        }
        write_json(staging_dir / "validation.json", validation)

    except (StagingError, OSError) as e:
        _write_staging_error(staging_dir, str(e))
        raise


# ======================================================
# EXCEL STAGING
# ======================================================
def run_excel_staging(
    file_hash: str,
    raw_excel_path: Path,
    staging_root: Path,
    parent_dir: Optional[str] = None,
) -> None:
    staging_dir = _prepare_staging_dir(staging_root, file_hash, parent_dir)

    try:
        try:
            profile = analyze_excel(raw_excel_path)
        except Exception as e:
            reason = f"Phân tích Excel thất bại: {e}"
            _write_staging_error(staging_dir, reason)
            raise StagingError(reason) from e

        write_json(staging_dir / "excel_profile.json", profile)

        validation = {
            "file_type": profile.get("file_type", "xlsx"),
            "requires_ocr": False,
            "has_tables": True, # Excel mặc định là bảng
            "recommended_pipeline": ["excel_table_extract"],
        }
        write_json(staging_dir / "validation.json", validation)

    except (StagingError, OSError) as e:
        _write_staging_error(staging_dir, str(e))
        raise

# lampx---------------------------------------------
# from pathlib import Path
# from typing import Optional

# from lakeflow.common.jsonio import write_json
# from lakeflow.pipelines.staging.pdf_analyzer import StagingError, analyze_pdf


# def _write_staging_error(staging_dir: Path, reason: str) -> None:
#     """Ghi lý do lỗi vào staging_error.txt để UI/người dùng xem sau."""
#     try:
#         staging_dir.mkdir(parents=True, exist_ok=True)
#         (staging_dir / "staging_error.txt").write_text(reason, encoding="utf-8")
#     except Exception:
#         pass


# def run_pdf_staging(
#     file_hash: str,
#     raw_pdf_path: Path,
#     staging_root: Path,
#     parent_dir: Optional[str] = None,
# ) -> None:
#     """
#     Chạy pipeline staging cho PDF (200_staging).

#     parent_dir: thư mục cha (domain) — output sẽ là 200_staging/<parent_dir>/<file_hash>/
#     Nếu không truyền: 200_staging/<file_hash>/ (giữ tương thích).

#     Sinh:
#       - pdf_profile.json
#       - validation.json
#       - (tuỳ chọn) text_sample.txt
#     """

#     if parent_dir:
#         staging_dir = staging_root / parent_dir / file_hash
#     else:
#         staging_dir = staging_root / file_hash

#     try:
#         staging_dir.mkdir(parents=True, exist_ok=True)

#         # ---------- 1. Analyze PDF ----------
#         try:
#             profile = analyze_pdf(raw_pdf_path)
#         except StagingError as e:
#             _write_staging_error(staging_dir, str(e))
#             raise
#         except Exception as e:
#             reason = f"Phân tích PDF thất bại: {e}"
#             _write_staging_error(staging_dir, reason)
#             raise StagingError(reason) from e

#         write_json(
#             staging_dir / "pdf_profile.json",
#             profile,
#         )

#         # ---------- 2. Build validation ----------
#         validation = {
#             "file_type": "pdf",
#             "requires_ocr": profile.get("is_scanned", False),
#             "has_tables": profile.get("has_tables", False),
#             "recommended_pipeline": ["pdf_text_extract"],
#         }

#         try:
#             write_json(
#                 staging_dir / "validation.json",
#                 validation,
#             )
#         except Exception as e:
#             reason = f"Ghi validation.json thất bại: {e}"
#             _write_staging_error(staging_dir, reason)
#             raise StagingError(reason) from e

#     except StagingError:
#         raise
#     except OSError as e:
#         reason = f"Lỗi ghi thư mục/file (quyền truy cập hoặc ổ đĩa): {e}"
#         _write_staging_error(staging_dir, reason)
#         raise StagingError(reason) from e
