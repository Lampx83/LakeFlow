# src/eduai/processing/staging/text_sampler.py
from pathlib import Path
from PyPDF2 import PdfReader


MAX_SAMPLE_CHARS = 1500


def extract_text_sample(path: Path) -> str:
    reader = PdfReader(str(path))
    buffer = ""

    for page in reader.pages[:2]:
        text = page.extract_text() or ""
        buffer += text.strip() + "\n"
        if len(buffer) >= MAX_SAMPLE_CHARS:
            break

    return buffer[:MAX_SAMPLE_CHARS].strip()
