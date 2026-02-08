# src/eduai/processing/staging/validator.py
from datetime import datetime


def validate_pdf(file_hash: str, profile: dict) -> dict:
    requires_ocr = profile["is_scanned_pdf"]
    requires_table_extraction = profile["has_text_layer"]
    requires_image_processing = profile["has_images"]

    pipeline = []

    if requires_ocr:
        pipeline.append("ocr_pdf")

    if profile["has_text_layer"]:
        pipeline.append("pdf_text_extract")

    if requires_table_extraction:
        pipeline.append("table_extraction")

    pipeline.append("text_normalization")

    return {
        "file_hash": file_hash,
        "file_type": "pdf",
        "analysis_time": datetime.utcnow().isoformat(),
        "requires_ocr": requires_ocr,
        "requires_table_extraction": requires_table_extraction,
        "requires_image_processing": requires_image_processing,
        "recommended_pipeline": pipeline,
        "confidence": 0.9,
        "notes": "Auto-generated validation from PDF structure analysis"
    }
