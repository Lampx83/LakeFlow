from pathlib import Path
from typing import Dict, Any, List

import pandas as pd

class StagingError(RuntimeError):
    """Staging error with clear reason, matches project logic."""

def analyze_excel(file_path: Path) -> Dict[str, Any]:
    """
    Analyze Excel (XLS/XLSX) file structure for pipeline decisions.
    Supports multiple engines to avoid missing dependency errors.
    """

    if not file_path.exists():
        raise StagingError(f"Excel file does not exist: {file_path}")

    # --------- Determine engine from file format ---------
    ext = file_path.suffix.lower()
    if ext == ".xls":
        engine = "xlrd"
    elif ext == ".xlsx" or ext == ".xlsm":
        engine = "openpyxl"
    else:
        engine = None  # Let pandas decide for other formats

    try:
        # --------- Load workbook metadata ---------
        excel = pd.ExcelFile(file_path, engine=engine)

        sheet_names: List[str] = excel.sheet_names
        sheet_count = len(sheet_names)

        if sheet_count == 0:
            raise StagingError("Excel file has no sheets.")

        # --------- Analyze first sheet (sample) ---------
        first_sheet = sheet_names[0]
        # Read first 5 rows to check data types
        df_sample = excel.parse(
            first_sheet,
            nrows=5
        )

        headers = list(df_sample.columns)
        column_count = len(headers)
        row_count_estimate = _estimate_row_count(file_path, first_sheet, engine)

        # Check data types in file
        has_numeric = any(
            pd.api.types.is_numeric_dtype(dtype)
            for dtype in df_sample.dtypes
        )

        has_text = any(
            pd.api.types.is_string_dtype(dtype)
            for dtype in df_sample.dtypes
        )

        return {
            "file_type": "xlsx" if ext == ".xlsx" else "xls",
            "sheet_count": sheet_count,
            "sheet_names": sheet_names,
            "primary_sheet": first_sheet,

            "column_count": column_count,
            "headers": [str(h) for h in headers],  # Ensure header is string for JSON
            "row_count_estimate": row_count_estimate,

            "has_numeric_data": has_numeric,
            "has_text_data": has_text,

            # Technical decisions for Step 2
            "requires_table_extraction": True,
            "requires_text_processing": False,
            "requires_ocr": False,
        }

    except ImportError as e:
        # Catch missing xlrd/openpyxl to report clearly in staging_error.txt
        missing_lib = "xlrd" if ext == ".xls" else "openpyxl"
        raise StagingError(f"Missing library for reading {ext}: Install '{missing_lib}'. Details: {e}")
    except Exception as e:
        raise StagingError(f"Excel analysis error: {str(e)}")


def _estimate_row_count(file_path: Path, sheet_name: str, engine: str) -> int:
    """
    Estimate row count without loading entire sheet into memory.
    """
    try:
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            usecols=[0],  # Read first column only
            engine=engine
        )
        return int(df.shape[0])
    except Exception:
        # Fallback if file too large or structure error
        return -1

# lampx-------------------------------------
# from pathlib import Path
# from typing import Dict, Any, List

# import pandas as pd


# def analyze_excel(file_path: Path) -> Dict[str, Any]:
#     """
#     Analyze Excel file structure for pipeline decisions (200_staging).
#
#     No business logic processing.
#     Does not load full data into memory unless needed.
#     """

#     if not file_path.exists():
#         raise FileNotFoundError(f"Excel file not found: {file_path}")

#     # --------- Load workbook metadata ---------
#     excel = pd.ExcelFile(file_path)

#     sheet_names: List[str] = excel.sheet_names
#     sheet_count = len(sheet_names)

#     # --------- Analyze first sheet (enough for staging) ---------
#     first_sheet = sheet_names[0]
#     df_sample = excel.parse(
#         first_sheet,
#         nrows=5  # take small sample only
#     )

#     headers = list(df_sample.columns)
#     column_count = len(headers)
#     row_count_estimate = _estimate_row_count(file_path, first_sheet)

#     has_numeric = any(
#         pd.api.types.is_numeric_dtype(dtype)
#         for dtype in df_sample.dtypes
#     )

#     has_text = any(
#         pd.api.types.is_string_dtype(dtype)
#         for dtype in df_sample.dtypes
#     )

#     return {
#         "file_type": "xlsx",
#         "sheet_count": sheet_count,
#         "sheet_names": sheet_names,
#         "primary_sheet": first_sheet,

#         "column_count": column_count,
#         "headers": headers,
#         "row_count_estimate": row_count_estimate,

#         "has_numeric_data": has_numeric,
#         "has_text_data": has_text,

#         # Technical decisions
#         "requires_table_extraction": True,
#         "requires_text_processing": False,
#         "requires_ocr": False,
#     }


# def _estimate_row_count(file_path: Path, sheet_name: str) -> int:
#     """
#     Estimate row count without loading entire sheet.
#     """
#     try:
#         df = pd.read_excel(
#             file_path,
#             sheet_name=sheet_name,
#             usecols=[0],  # read 1 column only
#         )
#         return int(df.shape[0])
#     except Exception:
#         # fallback if file too large / format error
#         return -1
