from pathlib import Path
from typing import Dict, Any, List

import pandas as pd


def analyze_excel(file_path: Path) -> Dict[str, Any]:
    """
    Phân tích cấu trúc file Excel để phục vụ quyết định pipeline (200_staging).

    Không xử lý nghiệp vụ.
    Không đọc toàn bộ dữ liệu vào memory nếu không cần.
    """

    if not file_path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    # --------- Load workbook metadata ---------
    excel = pd.ExcelFile(file_path)

    sheet_names: List[str] = excel.sheet_names
    sheet_count = len(sheet_names)

    # --------- Phân tích sheet đầu tiên (đủ cho staging) ---------
    first_sheet = sheet_names[0]
    df_sample = excel.parse(
        first_sheet,
        nrows=5  # chỉ lấy mẫu nhỏ
    )

    headers = list(df_sample.columns)
    column_count = len(headers)
    row_count_estimate = _estimate_row_count(file_path, first_sheet)

    has_numeric = any(
        pd.api.types.is_numeric_dtype(dtype)
        for dtype in df_sample.dtypes
    )

    has_text = any(
        pd.api.types.is_string_dtype(dtype)
        for dtype in df_sample.dtypes
    )

    return {
        "file_type": "xlsx",
        "sheet_count": sheet_count,
        "sheet_names": sheet_names,
        "primary_sheet": first_sheet,

        "column_count": column_count,
        "headers": headers,
        "row_count_estimate": row_count_estimate,

        "has_numeric_data": has_numeric,
        "has_text_data": has_text,

        # Quyết định kỹ thuật
        "requires_table_extraction": True,
        "requires_text_processing": False,
        "requires_ocr": False,
    }


def _estimate_row_count(file_path: Path, sheet_name: str) -> int:
    """
    Ước lượng số dòng mà không load toàn bộ sheet.
    """
    try:
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            usecols=[0],  # chỉ đọc 1 cột
        )
        return int(df.shape[0])
    except Exception:
        # fallback nếu file quá lớn / lỗi định dạng
        return -1
