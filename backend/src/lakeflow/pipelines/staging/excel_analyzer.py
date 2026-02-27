from pathlib import Path
from typing import Dict, Any, List

import pandas as pd

class StagingError(RuntimeError):
    """Lỗi staging với lý do rõ ràng, khớp với logic của dự án."""

def analyze_excel(file_path: Path) -> Dict[str, Any]:
    """
    Phân tích cấu trúc file Excel (XLS/XLSX) để phục vụ quyết định pipeline.
    Hỗ trợ đa engine để tránh lỗi thiếu dependency.
    """

    if not file_path.exists():
        raise StagingError(f"Excel file không tồn tại: {file_path}")

    # --------- Xác định Engine dựa trên định dạng file ---------
    ext = file_path.suffix.lower()
    if ext == ".xls":
        engine = "xlrd"
    elif ext == ".xlsx" or ext == ".xlsm":
        engine = "openpyxl"
    else:
        engine = None # Để pandas tự quyết định cho các định dạng khác

    try:
        # --------- Load workbook metadata ---------
        excel = pd.ExcelFile(file_path, engine=engine)

        sheet_names: List[str] = excel.sheet_names
        sheet_count = len(sheet_names)

        if sheet_count == 0:
            raise StagingError("File Excel không có sheet nào.")

        # --------- Phân tích sheet đầu tiên (Lấy mẫu) ---------
        first_sheet = sheet_names[0]
        # Đọc 5 dòng đầu để kiểm tra kiểu dữ liệu
        df_sample = excel.parse(
            first_sheet,
            nrows=5
        )

        headers = list(df_sample.columns)
        column_count = len(headers)
        row_count_estimate = _estimate_row_count(file_path, first_sheet, engine)

        # Kiểm tra loại dữ liệu có trong file
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
            "headers": [str(h) for h in headers], # Đảm bảo header là chuỗi để lưu JSON
            "row_count_estimate": row_count_estimate,

            "has_numeric_data": has_numeric,
            "has_text_data": has_text,

            # Quyết định kỹ thuật cho Step 2
            "requires_table_extraction": True,
            "requires_text_processing": False,
            "requires_ocr": False,
        }

    except ImportError as e:
        # Bắt lỗi thiếu xlrd hoặc openpyxl để báo cáo rõ ràng trong staging_error.txt
        missing_lib = "xlrd" if ext == ".xls" else "openpyxl"
        raise StagingError(f"Thiếu thư viện hỗ trợ đọc file {ext}: Hãy cài đặt '{missing_lib}'. Chi tiết: {e}")
    except Exception as e:
        raise StagingError(f"Lỗi phân tích Excel: {str(e)}")


def _estimate_row_count(file_path: Path, sheet_name: str, engine: str) -> int:
    """
    Ước lượng số dòng mà không load toàn bộ sheet vào memory.
    """
    try:
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            usecols=[0],  # Chỉ đọc cột đầu tiên
            engine=engine
        )
        return int(df.shape[0])
    except Exception:
        # Fallback nếu file quá lớn hoặc lỗi cấu trúc
        return -1

# lampx-------------------------------------
# from pathlib import Path
# from typing import Dict, Any, List

# import pandas as pd


# def analyze_excel(file_path: Path) -> Dict[str, Any]:
#     """
#     Phân tích cấu trúc file Excel để phục vụ quyết định pipeline (200_staging).

#     Không xử lý nghiệp vụ.
#     Không đọc toàn bộ dữ liệu vào memory nếu không cần.
#     """

#     if not file_path.exists():
#         raise FileNotFoundError(f"Excel file not found: {file_path}")

#     # --------- Load workbook metadata ---------
#     excel = pd.ExcelFile(file_path)

#     sheet_names: List[str] = excel.sheet_names
#     sheet_count = len(sheet_names)

#     # --------- Phân tích sheet đầu tiên (đủ cho staging) ---------
#     first_sheet = sheet_names[0]
#     df_sample = excel.parse(
#         first_sheet,
#         nrows=5  # chỉ lấy mẫu nhỏ
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

#         # Quyết định kỹ thuật
#         "requires_table_extraction": True,
#         "requires_text_processing": False,
#         "requires_ocr": False,
#     }


# def _estimate_row_count(file_path: Path, sheet_name: str) -> int:
#     """
#     Ước lượng số dòng mà không load toàn bộ sheet.
#     """
#     try:
#         df = pd.read_excel(
#             file_path,
#             sheet_name=sheet_name,
#             usecols=[0],  # chỉ đọc 1 cột
#         )
#         return int(df.shape[0])
#     except Exception:
#         # fallback nếu file quá lớn / lỗi định dạng
#         return -1
