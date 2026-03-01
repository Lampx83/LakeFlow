# backend/src/lakeflow/pipelines/processing/pipeline.py

from pathlib import Path
from typing import Dict, Any, Optional

from lakeflow.pipelines.processing.excel_pipeline import run_excel_pipeline
from lakeflow.pipelines.processing.pdf_pipeline import run_pdf_pipeline
from lakeflow.pipelines.processing.word_pipeline import run_word_pipeline
from lakeflow.common.jsonio import read_json


class ProcessedPipelineError(RuntimeError):
    """Error in 300_processed pipeline."""


REQUIRED_OUTPUT_FILES = {
    "clean_text.txt",
    "sections.json",
    "chunks.json",
    "tables.json",
}


def run_processed_pipeline(
    file_hash: str,
    raw_file_path: Path,
    staging_dir: Path,
    processed_root: Path,
    force: bool = False,
    parent_dir: Optional[str] = None,
) -> None:
    """
    Orchestrator for 300_processed step.
    """

    print(f"[300] Start processing: {file_hash}")

    # ---------- 1. Validate input ----------
    if not raw_file_path.exists():
        raise ProcessedPipelineError(f"Raw file not found: {raw_file_path}")

    validation_file = staging_dir / "validation.json"
    if not validation_file.exists():
        raise ProcessedPipelineError(f"Missing validation.json for file {file_hash}")

    validation: Dict[str, Any] = read_json(validation_file)

    file_type = validation.get("file_type")
    if not file_type:
        raise ProcessedPipelineError("validation.json missing 'file_type'")

    # ---------- 2. Prepare output directory ----------
    if parent_dir:
        out_dir = processed_root / parent_dir / file_hash
    else:
        out_dir = processed_root / file_hash

    if out_dir.exists() and not force:
        existing = {p.name for p in out_dir.iterdir() if p.is_file()}
        if REQUIRED_OUTPUT_FILES.issubset(existing):
            print(f"[300] Skip (already processed): {file_hash}")
            return

    out_dir.mkdir(parents=True, exist_ok=True)

    # ---------- 3. Dispatch by file type ----------
    print(f"[300] File type: {file_type}")

    # Support both xlsx and xls
    if file_type in ["xlsx", "xls"]:
        run_excel_pipeline(
            file_hash=file_hash,
            raw_file_path=raw_file_path,
            output_dir=out_dir,
            validation=validation,
        )

    elif file_type == "pdf":
        run_pdf_pipeline(
            file_hash=file_hash,
            raw_file_path=raw_file_path,
            output_dir=out_dir,
            validation=validation,
        )

    # Word processing branch
    elif file_type == "docx":
        run_word_pipeline(
            file_hash=file_hash,
            raw_file_path=raw_file_path,
            output_dir=out_dir,
            validation=validation,
        )

    else:
        raise ProcessedPipelineError(f"Unsupported file_type: {file_type}")

    # ---------- 4. Validate output contract ----------
    produced = {p.name for p in out_dir.iterdir() if p.is_file()}
    missing = REQUIRED_OUTPUT_FILES - produced

    if missing:
        # Note: Some Word/Excel files may not extract tables,
        # but table_analyzer should still create empty tables.json []
        # to pass this contract check.
        raise ProcessedPipelineError(
            f"Processed output incomplete for {file_hash}, missing: {missing}"
        )

    print(f"[300] Completed successfully: {file_hash}")


# lampx------------------------
# # src/lakeflow/processing/processing/pipeline.py

# from pathlib import Path
# from typing import Dict, Any, Optional

# from lakeflow.pipelines.processing.excel_pipeline import run_excel_pipeline
# from lakeflow.pipelines.processing.pdf_pipeline import run_pdf_pipeline
# from lakeflow.common.jsonio import read_json


# class ProcessedPipelineError(RuntimeError):
#     """Error in 300_processed pipeline."""


# REQUIRED_OUTPUT_FILES = {
#     "clean_text.txt",
#     "sections.json",
#     "chunks.json",
#     "tables.json",
# }


# def run_processed_pipeline(
#     file_hash: str,
#     raw_file_path: Path,
#     staging_dir: Path,
#     processed_root: Path,
#     force: bool = False,
#     parent_dir: Optional[str] = None,
# ) -> None:
#     """
#     Orchestrator for 300_processed step.
#
#     parent_dir: parent directory (domain) — output will be 300_processed/<parent_dir>/<file_hash>/
#     If not passed: 300_processed/<file_hash>/ (keep compatibility).
#
#     Parameters
#     ----------
#     file_hash : str
#         Hash of source file
#     raw_file_path : Path
#         File path in 100_raw
#     staging_dir : Path
#         Directory 200_staging/<domain>/<file_hash> or 200_staging/<file_hash>
#     processed_root : Path
#         Root of 300_processed
#     force : bool
#         True to reprocess even if processing data exists
#     parent_dir : str, optional
#         Parent directory (domain) for output 300_processed/<parent_dir>/<file_hash>/
#     """

#     print(f"[300] Start processing: {file_hash}")

#     # ---------- 1. Validate input ----------
#     if not raw_file_path.exists():
#         raise ProcessedPipelineError(
#             f"Raw file not found: {raw_file_path}"
#         )

#     validation_file = staging_dir / "validation.json"
#     if not validation_file.exists():
#         raise ProcessedPipelineError(
#             f"Missing validation.json for file {file_hash}"
#         )

#     validation: Dict[str, Any] = read_json(validation_file)

#     file_type = validation.get("file_type")
#     if not file_type:
#         raise ProcessedPipelineError(
#             "validation.json missing 'file_type'"
#         )

#     # ---------- 2. Prepare output directory ----------
#     if parent_dir:
#         out_dir = processed_root / parent_dir / file_hash
#     else:
#         out_dir = processed_root / file_hash

#     if out_dir.exists() and not force:
#         existing = {p.name for p in out_dir.iterdir() if p.is_file()}
#         if REQUIRED_OUTPUT_FILES.issubset(existing):
#             print(f"[300] Skip (already processing): {file_hash}")
#             return

#     out_dir.mkdir(parents=True, exist_ok=True)

#     # ---------- 3. Dispatch by file type ----------
#     print(f"[300] File type: {file_type}")

#     if file_type == "xlsx":
#         run_excel_pipeline(
#             file_hash=file_hash,
#             raw_file_path=raw_file_path,
#             output_dir=out_dir,
#             validation=validation,
#         )

#     elif file_type == "pdf":
#         run_pdf_pipeline(
#             file_hash=file_hash,
#             raw_file_path=raw_file_path,
#             output_dir=out_dir,
#             validation=validation,
#         )

#     else:
#         raise ProcessedPipelineError(
#             f"Unsupported file_type: {file_type}"
#         )

#     # ---------- 4. Validate output contract ----------
#     produced = {p.name for p in out_dir.iterdir() if p.is_file()}
#     missing = REQUIRED_OUTPUT_FILES - produced

#     if missing:
#         raise ProcessedPipelineError(
#             f"Processed output incomplete for {file_hash}, missing: {missing}"
#         )

#     print(f"[300] Completed successfully: {file_hash}")
