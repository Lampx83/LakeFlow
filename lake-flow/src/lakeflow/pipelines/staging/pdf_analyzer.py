from pathlib import Path

from PyPDF2 import PdfReader
from PyPDF2.generic import IndirectObject, DictionaryObject

# PyPDF2/pypdf exceptions for clearer error messages
try:
    from PyPDF2.errors import PdfReadError, PdfStreamError
except ImportError:
    try:
        from pypdf.errors import PdfReadError, PdfStreamError
    except ImportError:
        PdfReadError = Exception
        PdfStreamError = Exception


class StagingError(RuntimeError):
    """Lỗi staging với lý do rõ ràng."""


def _resolve(obj):
    """
    Resolve PyPDF2 IndirectObject to actual object.
    """
    if isinstance(obj, IndirectObject):
        return obj.get_object()
    return obj


def analyze_pdf(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        raise StagingError(f"File không tồn tại: {path}")
    if not path.is_file():
        raise StagingError(f"Đường dẫn không phải file: {path}")

    try:
        reader = PdfReader(str(path))
    except (PdfReadError, PdfStreamError) as e:
        msg = str(e).strip()
        if "encrypt" in msg.lower() or "password" in msg.lower():
            raise StagingError(f"PDF bị mã hóa hoặc yêu cầu mật khẩu: {msg}") from e
        if "%PDF-" in msg or "expected" in msg.lower():
            raise StagingError(f"File không đúng định dạng PDF (có thể hỏng hoặc không phải PDF): {msg}") from e
        raise StagingError(f"Đọc PDF thất bại: {msg}") from e
    except Exception as e:
        msg = str(e).strip()
        raise StagingError(f"Lỗi phân tích PDF: {msg}") from e

    page_count = len(reader.pages)
    text_pages = 0
    image_pages = 0

    try:
        for page in reader.pages:
            # -------- Text layer detection --------
            text = page.extract_text()
            if text and text.strip():
                text_pages += 1

            # -------- Image / XObject detection --------
            resources = _resolve(page.get("/Resources"))

            if isinstance(resources, DictionaryObject):
                xobjects = _resolve(resources.get("/XObject"))
                if isinstance(xobjects, DictionaryObject):
                    image_pages += 1
    except Exception as e:
        raise StagingError(f"Lỗi khi đọc trang PDF: {e}") from e

    has_text_layer = text_pages > 0
    is_scanned_pdf = not has_text_layer

    metadata = reader.metadata or {}

    return {
        "file_type": "pdf",
        "page_count": page_count,
        "has_text_layer": has_text_layer,
        "text_page_ratio": round(text_pages / page_count, 2) if page_count else 0,
        "has_images": image_pages > 0,
        "is_scanned_pdf": is_scanned_pdf,
        "producer": metadata.get("/Producer"),
        "creator": metadata.get("/Creator"),
        "pdf_version": reader.pdf_header
    }
