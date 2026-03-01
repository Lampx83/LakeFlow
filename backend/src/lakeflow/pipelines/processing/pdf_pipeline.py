import re
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import easyocr

from lakeflow.pipelines.processing.chunking import chunk_text
from lakeflow.common.jsonio import write_json


# ==========================================================
# GLOBAL OCR READER (LOAD ONCE)
# ==========================================================

READER = None


# ==========================================================
# TEXT NORMALIZATION
# ==========================================================

def normalize_text(text: str) -> str:
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"([A-Za-zÀ-ỹ])(\d)", r"\1 \2", text)
    return text.strip()


# ==========================================================
# OCR OPTIMIZED
# ==========================================================

def perform_ocr_optimized(pdf_path: Path, max_pages: int = 10) -> str:
    global READER

    if READER is None:
        READER = easyocr.Reader(["vi", "en"], gpu=False)

    images = convert_from_path(
        pdf_path,
        dpi=200,
        last_page=max_pages,
        thread_count=2,
    )

    ocr_text = ""

    for image in images:
        img_array = np.array(image)
        results = READER.readtext(img_array, detail=0)
        ocr_text += " ".join(results) + "\n"

    return ocr_text


# ==========================================================
# MAIN PIPELINE
# ==========================================================

def run_pdf_pipeline(
    file_hash: str,
    raw_file_path: Path,
    output_dir: Path,
    validation: Dict[str, Any],
) -> None:

    output_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(raw_file_path))

    pages_text: List[str] = []

    # ------------------------------------------------------
    # 1️⃣ Try extract text layer
    # ------------------------------------------------------

    for page in reader.pages:
        try:
            text = page.extract_text() or ""
            if text.strip():
                pages_text.append(text.strip())
        except Exception:
            continue

    full_text = "\n\n".join(pages_text)

    # ------------------------------------------------------
    # 2️⃣ OCR fallback
    # ------------------------------------------------------

    is_scanned = False

    if not full_text.strip():
        full_text = perform_ocr_optimized(raw_file_path, max_pages=10)
        is_scanned = True

    full_text = normalize_text(full_text)

    # ------------------------------------------------------
    # 3️⃣ clean_text.txt
    # ------------------------------------------------------

    (output_dir / "clean_text.txt").write_text(
        full_text,
        encoding="utf-8",
    )

    # ------------------------------------------------------
    # 4️⃣ sections.json (page-aware)
    # ------------------------------------------------------

    sections = [
        {
            "section_id": "main_content",
            "title": "PDF document content",
            "level": 1,
        }
    ]

    write_json(output_dir / "sections.json", sections)

    # ------------------------------------------------------
    # 5️⃣ tables.json (PDF does not parse tables here)
    # ------------------------------------------------------

    write_json(output_dir / "tables.json", [])

    # ------------------------------------------------------
    # 6️⃣ chunks.json
    # ------------------------------------------------------

    chunks = []

    if full_text:
        text_chunks = chunk_text(
            full_text,
            chunk_size=800,
            chunk_overlap=100,
        )

        for i, c in enumerate(text_chunks, 1):
            chunks.append({
                "chunk_id": f"{file_hash}_c{i}",
                "text": c,
                "section_id": "main_content",
                "file_hash": file_hash,
                "token_estimate": len(c.split()),
            })

    write_json(output_dir / "chunks.json", chunks)

    print(f"[PROCESS][PDF] {raw_file_path.name} "
          f"{'(OCR)' if is_scanned else ''} → {len(chunks)} chunks.")
    
    
# legacy before 23/2/2026 =================
# import json
# import numpy as np
# from pathlib import Path
# from typing import Dict, Any
# from PyPDF2 import PdfReader
# from pdf2image import convert_from_path
# import easyocr

# from lakeflow.pipelines.processing.chunking import chunk_text
# from lakeflow.common.jsonio import write_json

# # Initialize global Reader to avoid repeated loading
# READER = None 

# def perform_ocr_optimized(pdf_path: Path, max_pages: int = 10) -> str:
#     """Optimized OCR: Limit pages and reduce DPI for faster execution"""
#     global READER
#     if READER is None:
#         # Load model into RAM once only
#         READER = easyocr.Reader(['vi', 'en'], gpu=False) # Set gpu=True if you have NVIDIA card
#
#     # 1. Convert PDF to images with lower DPI (200 vs 300) for faster processing
#     # 2. Take only first max_pages to save time
#     images = convert_from_path(
#         pdf_path, 
#         dpi=200, 
#         last_page=max_pages,
#         thread_count=2 # Use multithreading for faster image render
#     )
    
#     ocr_text = ""
#     for i, image in enumerate(images):
#         img_array = np.array(image)
#         # detail=0 returns plain text faster
#         results = READER.readtext(img_array, detail=0) 
#         ocr_text += " ".join(results) + "\n"
        
#     return ocr_text

# def run_pdf_pipeline(file_hash: str, raw_file_path: Path, output_dir: Path, validation: Dict[str, Any]) -> None:
#     output_dir.mkdir(parents=True, exist_ok=True)
    
#     # Prefer reading Text Layer (very fast)
#     reader = PdfReader(str(raw_file_path))
#     full_text = ""
#     try:
#         for page in reader.pages:
#             t = page.extract_text()
#             if t: full_text += t + "\n"
#     except:
#         pass

#     # Run OCR only when text layer is empty
#     is_scanned = False
#     if not full_text.strip():
#         # Limit to first 10 pages so AI gets context without hanging Server
#         full_text = perform_ocr_optimized(raw_file_path, max_pages=10)
#         is_scanned = True

#     # Save result
#     (output_dir / "clean_text.txt").write_text(full_text, encoding="utf-8")
#     write_json(output_dir / "sections.json", [{"section_id": "main", "title": "Content", "level": 1}])
#     write_json(output_dir / "tables.json", [])

#     chunks = []
#     if full_text.strip():
#         # Slightly increase chunk_size to reduce chunks for embedding step
#         text_chunks = chunk_text(full_text, chunk_size=800, chunk_overlap=100)
#         chunks = [{"chunk_id": f"{file_hash}_c{i}", "text": c, "file_hash": file_hash} for i, c in enumerate(text_chunks)]
    
#     write_json(output_dir / "chunks.json", chunks)
#     print(f"   [DONE] PDF {'(OCR)' if is_scanned else ''}: {len(chunks)} chunks.")


# # lampx---------------------------------------------
# # from pathlib import Path
# # from typing import Dict, Any, List

# # from PyPDF2 import PdfReader

# # from lakeflow.common.jsonio import write_json


# # def run_pdf_pipeline(
# #     file_hash: str,
# #     raw_file_path: Path,
# #     output_dir: Path,
# #     validation: Dict[str, Any],
# # ) -> None:
# #     """
# #     Process text-based PDF → produce AI-ready data (300_processed)
# #     """

# #     reader = PdfReader(str(raw_file_path))

# #     pages_text: List[str] = []
# #     for page in reader.pages:
# #         text = page.extract_text() or ""
# #         if text.strip():
# #             pages_text.append(text.strip())

# #     full_text = "\n\n".join(pages_text)

# #     # ---------- clean_text.txt ----------
# #     (output_dir / "clean_text.txt").write_text(
# #         full_text,
# #         encoding="utf-8",
# #     )

# #     # ---------- sections.json ----------
# #     sections = [
# #         {
# #             "section_id": "full_document",
# #             "title": "Full PDF content",
# #             "level": 1,
# #         }
# #     ]
# #     write_json(output_dir / "sections.json", sections)

# #     # ---------- chunks.json ----------
# #     chunks = []
# #     chunk_size = 500  # words

# #     words = full_text.split()
# #     for i in range(0, len(words), chunk_size):
# #         chunk_text = " ".join(words[i : i + chunk_size])
# #         chunks.append(
# #             {
# #                 "chunk_id": f"{file_hash}_c{i//chunk_size + 1}",
# #                 "text": chunk_text,
# #                 "section_id": "full_document",
# #                 "file_hash": file_hash,
# #                 "token_estimate": len(chunk_text.split()),
# #             }
# #         )

# #     write_json(output_dir / "chunks.json", chunks)

# #     # ---------- tables.json ----------
# #     write_json(output_dir / "tables.json", [])
