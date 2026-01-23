from pathlib import Path
from PyPDF2 import PdfReader
from PyPDF2.generic import IndirectObject, DictionaryObject


def _resolve(obj):
    """
    Resolve PyPDF2 IndirectObject to actual object.
    """
    if isinstance(obj, IndirectObject):
        return obj.get_object()
    return obj


def analyze_pdf(path: Path) -> dict:
    reader = PdfReader(str(path))

    page_count = len(reader.pages)
    text_pages = 0
    image_pages = 0

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
