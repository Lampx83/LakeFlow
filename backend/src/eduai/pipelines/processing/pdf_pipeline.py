from pathlib import Path
from typing import Dict, Any, List

from PyPDF2 import PdfReader

from eduai.common.jsonio import write_json


def run_pdf_pipeline(
    file_hash: str,
    raw_file_path: Path,
    output_dir: Path,
    validation: Dict[str, Any],
) -> None:
    """
    Xử lý PDF text-based → sinh dữ liệu AI-ready (300_processed)
    """

    reader = PdfReader(str(raw_file_path))

    pages_text: List[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages_text.append(text.strip())

    full_text = "\n\n".join(pages_text)

    # ---------- clean_text.txt ----------
    (output_dir / "clean_text.txt").write_text(
        full_text,
        encoding="utf-8",
    )

    # ---------- sections.json ----------
    sections = [
        {
            "section_id": "full_document",
            "title": "Toàn bộ nội dung PDF",
            "level": 1,
        }
    ]
    write_json(output_dir / "sections.json", sections)

    # ---------- chunks.json ----------
    chunks = []
    chunk_size = 500  # từ

    words = full_text.split()
    for i in range(0, len(words), chunk_size):
        chunk_text = " ".join(words[i : i + chunk_size])
        chunks.append(
            {
                "chunk_id": f"{file_hash}_c{i//chunk_size + 1}",
                "text": chunk_text,
                "section_id": "full_document",
                "file_hash": file_hash,
                "token_estimate": len(chunk_text.split()),
            }
        )

    write_json(output_dir / "chunks.json", chunks)

    # ---------- tables.json ----------
    write_json(output_dir / "tables.json", [])
