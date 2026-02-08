from pathlib import Path
from typing import Dict, Any, List

import pandas as pd

from eduai.common.jsonio import write_json


def run_excel_pipeline(
    file_hash: str,
    raw_file_path: Path,
    output_dir: Path,
    validation: Dict[str, Any],
) -> None:
    """
    Xử lý Excel → sinh dữ liệu AI-ready (300_processed)
    """

    # ---------- 1. Load Excel ----------
    excel = pd.ExcelFile(raw_file_path)
    primary_sheet = validation.get("primary_sheet") or excel.sheet_names[0]

    df = excel.parse(primary_sheet)
    df = df.dropna(how="all")

    # ---------- 2. Build tables.json ----------
    table = {
        "table_id": f"{file_hash}_table_1",
        "title": f"Dữ liệu từ sheet '{primary_sheet}'",
        "headers": list(df.columns),
        "row_count": int(df.shape[0]),
        "rows": df.fillna("").values.tolist(),
        "source_sheet": primary_sheet,
        "source_file": raw_file_path.name,
    }

    tables: List[Dict[str, Any]] = [table]

    write_json(output_dir / "tables.json", tables)

    # ---------- 3. Build clean_text.txt ----------
    clean_text = (
        f"Tài liệu bảng dữ liệu trích xuất từ file Excel '{raw_file_path.name}'.\n"
        f"Sheet chính: {primary_sheet}.\n"
        f"Số dòng dữ liệu: {df.shape[0]}.\n"
        f"Số cột: {df.shape[1]}.\n"
        f"Các cột bao gồm: {', '.join(df.columns)}."
    )

    (output_dir / "clean_text.txt").write_text(
        clean_text,
        encoding="utf-8",
    )

    # ---------- 4. Build sections.json ----------
    sections = [
        {
            "section_id": "overview",
            "title": "Tổng quan bảng dữ liệu",
            "level": 1,
        }
    ]

    write_json(output_dir / "sections.json", sections)

    # ---------- 5. Build chunks.json ----------
    chunks = [
        {
            "chunk_id": f"{file_hash}_c1",
            "text": clean_text,
            "section_id": "overview",
            "file_hash": file_hash,
            "token_estimate": len(clean_text.split()),
        }
    ]

    write_json(output_dir / "chunks.json", chunks)
