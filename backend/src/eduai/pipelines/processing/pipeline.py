# src/eduai/processing/processing/pipeline.py

from pathlib import Path
from typing import Dict, Any, Optional

from eduai.pipelines.processing.excel_pipeline import run_excel_pipeline
from eduai.pipelines.processing.pdf_pipeline import run_pdf_pipeline
from eduai.common.jsonio import read_json


class ProcessedPipelineError(RuntimeError):
    """Lỗi trong pipeline 300_processed."""


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
    Orchestrator cho bước 300_processed.

    parent_dir: thư mục cha (domain) — output sẽ là 300_processed/<parent_dir>/<file_hash>/
    Nếu không truyền: 300_processed/<file_hash>/ (giữ tương thích).

    Parameters
    ----------
    file_hash : str
        Hash của file gốc
    raw_file_path : Path
        Đường dẫn file trong 100_raw
    staging_dir : Path
        Thư mục 200_staging/<domain>/<file_hash> hoặc 200_staging/<file_hash>
    processed_root : Path
        Root của 300_processed
    force : bool
        True để xử lý lại dù đã có processing data
    parent_dir : str, optional
        Thư mục cha (domain) để ghi 300_processed/<parent_dir>/<file_hash>/
    """

    print(f"[300] Start processing: {file_hash}")

    # ---------- 1. Validate input ----------
    if not raw_file_path.exists():
        raise ProcessedPipelineError(
            f"Raw file not found: {raw_file_path}"
        )

    validation_file = staging_dir / "validation.json"
    if not validation_file.exists():
        raise ProcessedPipelineError(
            f"Missing validation.json for file {file_hash}"
        )

    validation: Dict[str, Any] = read_json(validation_file)

    file_type = validation.get("file_type")
    if not file_type:
        raise ProcessedPipelineError(
            "validation.json missing 'file_type'"
        )

    # ---------- 2. Prepare output directory ----------
    if parent_dir:
        out_dir = processed_root / parent_dir / file_hash
    else:
        out_dir = processed_root / file_hash

    if out_dir.exists() and not force:
        existing = {p.name for p in out_dir.iterdir() if p.is_file()}
        if REQUIRED_OUTPUT_FILES.issubset(existing):
            print(f"[300] Skip (already processing): {file_hash}")
            return

    out_dir.mkdir(parents=True, exist_ok=True)

    # ---------- 3. Dispatch by file type ----------
    print(f"[300] File type: {file_type}")

    if file_type == "xlsx":
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

    else:
        raise ProcessedPipelineError(
            f"Unsupported file_type: {file_type}"
        )

    # ---------- 4. Validate output contract ----------
    produced = {p.name for p in out_dir.iterdir() if p.is_file()}
    missing = REQUIRED_OUTPUT_FILES - produced

    if missing:
        raise ProcessedPipelineError(
            f"Processed output incomplete for {file_hash}, missing: {missing}"
        )

    print(f"[300] Completed successfully: {file_hash}")
