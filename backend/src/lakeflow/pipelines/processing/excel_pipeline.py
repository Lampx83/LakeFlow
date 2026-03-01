from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import re

from lakeflow.common.jsonio import write_json
from lakeflow.pipelines.processing.chunking import chunk_text


# ==========================================================
# TEXT NORMALIZATION
# ==========================================================

def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"([A-Za-zÀ-ỹ])(\d)", r"\1 \2", text)
    return text.strip()


# ==========================================================
# MAIN PIPELINE
# ==========================================================

def run_excel_pipeline(
    file_hash: str,
    raw_file_path: Path,
    output_dir: Path,
    validation: Dict[str, Any],
) -> None:

    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------
    # 1️⃣ Load Excel
    # ------------------------------------------------------

    excel = pd.ExcelFile(raw_file_path)
    primary_sheet = validation.get("primary_sheet") or excel.sheet_names[0]

    df = excel.parse(primary_sheet)
    df = df.dropna(how="all")
    df_filled = df.fillna("")

    # ------------------------------------------------------
    # 2️⃣ tables.json
    # ------------------------------------------------------

    table = {
        "table_id": f"{file_hash}_table_1",
        "title": f"Data from sheet '{primary_sheet}'",
        "headers": list(df.columns),
        "row_count": int(df.shape[0]),
        "rows": df_filled.values.tolist(),
        "source_sheet": primary_sheet,
        "source_file": raw_file_path.name,
    }

    write_json(output_dir / "tables.json", [table])

    # ------------------------------------------------------
    # 3️⃣ Build Narrative Text
    # ------------------------------------------------------

    overview_text = normalize_text(
        f"""
        Tabular data extracted from Excel file '{raw_file_path.name}'.
        Primary sheet: {primary_sheet}.
        Row count: {df.shape[0]}.
        Column count: {df.shape[1]}.
        Columns: {', '.join(df.columns)}.
        """
    )

    rows_detail: List[str] = []

    for i, row in df_filled.iterrows():
        items = [
            f"{col}: {val}"
            for col, val in row.items()
            if str(val).strip()
        ]

        if items:
            row_text = f"Row {i+1}. " + "; ".join(items)
            rows_detail.append(normalize_text(row_text))

    detailed_text = "\n".join(rows_detail)

    full_clean_text = overview_text + "\n\nData details:\n" + detailed_text

    (output_dir / "clean_text.txt").write_text(
        full_clean_text,
        encoding="utf-8",
    )

    # ------------------------------------------------------
    # 4️⃣ sections.json
    # ------------------------------------------------------

    sections = [
        {
            "section_id": "overview",
            "title": "Table data overview",
            "level": 1,
        },
        {
            "section_id": "data_rows",
            "title": "Row details",
            "level": 1,
        },
    ]

    write_json(output_dir / "sections.json", sections)

    # ------------------------------------------------------
    # 5️⃣ chunks.json (Token-aware)
    # ------------------------------------------------------

    chunks = []
    chunk_index = 0

    # ---- Chunk Overview ----
    chunks.append({
        "chunk_id": f"{file_hash}_c_ov",
        "text": overview_text,
        "section_id": "overview",
        "file_hash": file_hash,
        "token_estimate": len(overview_text.split()),
    })

    # ---- Chunk Data Rows (token-based) ----
    data_chunks = chunk_text(
        detailed_text,
        chunk_size=600,
        chunk_overlap=100,
    )

    for chunk in data_chunks:
        chunk_index += 1
        chunks.append({
            "chunk_id": f"{file_hash}_c_d{chunk_index}",
            "text": chunk,
            "section_id": "data_rows",
            "file_hash": file_hash,
            "token_estimate": len(chunk.split()),
        })

    write_json(output_dir / "chunks.json", chunks)

    print(f"[PROCESS][EXCEL] {raw_file_path.name} → {len(chunks)} chunks created.")

# legacy before 23/2/2026
# from pathlib import Path
# from typing import Dict, Any, List
# import pandas as pd

# from lakeflow.common.jsonio import write_json
# # from lakeflow.pipelines.processing.chunking import chunk_text


# def run_excel_pipeline(
#     file_hash: str,
#     raw_file_path: Path,
#     output_dir: Path,
#     validation: Dict[str, Any],
# ) -> None:
#     """
#     Process Excel → produce AI-ready data (300_processed).
#     Upgraded version: Extract row-level detail for accurate AI responses.
#     """

#     # ---------- 1. Load Excel ----------
#     excel = pd.ExcelFile(raw_file_path)
#     primary_sheet = validation.get("primary_sheet") or excel.sheet_names[0]

#     df = excel.parse(primary_sheet)
#     df = df.dropna(how="all")
#     # Replace NaN with empty string to avoid JSON errors
#     df_filled = df.fillna("")

#     # ---------- 2. Build tables.json (Keep previous structure) ----------
#     table = {
#         "table_id": f"{file_hash}_table_1",
#         "title": f"Data from sheet '{primary_sheet}'",
#         "headers": list(df.columns),
#         "row_count": int(df.shape[0]),
#         "rows": df_filled.values.tolist(),
#         "source_sheet": primary_sheet,
#         "source_file": raw_file_path.name,
#     }
#     write_json(output_dir / "tables.json", [table])

#     # ---------- 3. Build narrative text detail ----------
#     # Create overview section
#     overview_text = (
#         f"Tabular data extracted from Excel file '{raw_file_path.name}'.\n"
#         f"Primary sheet: {primary_sheet}.\n"
#         f"Row count: {df.shape[0]}.\n"
#         f"Column count: {df.shape[1]}.\n"
#         f"Columns: {', '.join(df.columns)}."
#     )

#     # Create row-level detail description
#     rows_detail = []
#     for i, row in df_filled.iterrows():
#         # Create sentence: "Row 1: Col A is Value A, Col B is Value B..."
#         items = [f"{col}: {val}" for col, val in row.items() if str(val).strip()]
#         rows_detail.append(f"Row {i+1}: " + ", ".join(items))
    
#     detailed_text = "\n".join(rows_detail)
#     full_clean_text = overview_text + "\n\nData details:\n" + detailed_text

#     # Save clean_text.txt
#     (output_dir / "clean_text.txt").write_text(full_clean_text, encoding="utf-8")

#     # ---------- 4. Build sections.json (Keep previous structure) ----------
#     sections = [
#         {
#             "section_id": "overview",
#             "title": "Table data overview",
#             "level": 1,
#         },
#         {
#             "section_id": "data_rows",
#             "title": "Row details",
#             "level": 1,
#         }
#     ]
#     write_json(output_dir / "sections.json", sections)

#     # ---------- 5. Build chunks.json (Improved to hold actual data) ----------
#     chunks = []
    
#     # Chunk 1: Overview
#     chunks.append({
#         "chunk_id": f"{file_hash}_c_ov",
#         "text": overview_text,
#         "section_id": "overview",
#         "file_hash": file_hash,
#         "token_estimate": len(overview_text.split()),
#     })

#     # Chunk 2+: Split detail data (avoid exceeding LLM token limit)
#     # Group ~20 rows per chunk
#     batch_size = 20
#     for i in range(0, len(rows_detail), batch_size):
#         batch = rows_detail[i : i + batch_size]
#         chunk_body = f"Data from file {raw_file_path.name}, sheet {primary_sheet} (continued):\n" + "\n".join(batch)
        
#         chunks.append({
#             "chunk_id": f"{file_hash}_c_d{i//batch_size + 1}",
#             "text": chunk_body,
#             "section_id": "data_rows",
#             "file_hash": file_hash,
#             "token_estimate": len(chunk_body.split()),
#         })

#     write_json(output_dir / "chunks.json", chunks)

    
# # lampx---------------------------------------------------------------------
# # from pathlib import Path
# # from typing import Dict, Any, List

# # import pandas as pd

# # from lakeflow.common.jsonio import write_json


# # def run_excel_pipeline(
# #     file_hash: str,
# #     raw_file_path: Path,
# #     output_dir: Path,
# #     validation: Dict[str, Any],
# # ) -> None:
# #     """
# #     Process Excel → produce AI-ready data (300_processed)
# #     """

# #     # ---------- 1. Load Excel ----------
# #     excel = pd.ExcelFile(raw_file_path)
# #     primary_sheet = validation.get("primary_sheet") or excel.sheet_names[0]

# #     df = excel.parse(primary_sheet)
# #     df = df.dropna(how="all")

# #     # ---------- 2. Build tables.json ----------
# #     table = {
# #         "table_id": f"{file_hash}_table_1",
# #         "title": f"Data from sheet '{primary_sheet}'",
# #         "headers": list(df.columns),
# #         "row_count": int(df.shape[0]),
# #         "rows": df.fillna("").values.tolist(),
# #         "source_sheet": primary_sheet,
# #         "source_file": raw_file_path.name,
# #     }

# #     tables: List[Dict[str, Any]] = [table]

# #     write_json(output_dir / "tables.json", tables)

# #     # ---------- 3. Build clean_text.txt ----------
# #     clean_text = (
# #         f"Tabular data extracted from Excel file '{raw_file_path.name}'.\n"
# #         f"Primary sheet: {primary_sheet}.\n"
# #         f"Row count: {df.shape[0]}.\n"
# #         f"Column count: {df.shape[1]}.\n"
# #         f"Columns: {', '.join(df.columns)}."
# #     )

# #     (output_dir / "clean_text.txt").write_text(
# #         clean_text,
# #         encoding="utf-8",
# #     )

# #     # ---------- 4. Build sections.json ----------
# #     sections = [
# #         {
# #             "section_id": "overview",
# #             "title": "Table data overview",
# #             "level": 1,
# #         }
# #     ]

# #     write_json(output_dir / "sections.json", sections)

# #     # ---------- 5. Build chunks.json ----------
# #     chunks = [
# #         {
# #             "chunk_id": f"{file_hash}_c1",
# #             "text": clean_text,
# #             "section_id": "overview",
# #             "file_hash": file_hash,
# #             "token_estimate": len(clean_text.split()),
# #         }
# #     ]

# #     write_json(output_dir / "chunks.json", chunks)
