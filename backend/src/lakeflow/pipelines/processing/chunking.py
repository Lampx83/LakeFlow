"""
Chunking module for LakeFlow AI ingestion pipeline.

Goals:
- Semantic-friendly chunking
- Avoid creating too-small chunks
- Support overlap to improve RAG recall
- Normalize text before chunking
"""

import re
from typing import List


# ==========================================================
# TEXT NORMALIZATION
# ==========================================================

def _normalize_text(text: str) -> str:
    """
    Normalize text before chunking:
    - Merge multiple whitespace
    - Normalize newlines
    - Fix text stuck to numbers (e.g. word3 → word 3)
    """

    if not text:
        return ""

    # Normalize newlines
    text = re.sub(r"\r\n", "\n", text)

    # Merge multiple spaces into one
    text = re.sub(r"[ \t]+", " ", text)

    # Remove consecutive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Fix text stuck to numbers
    text = re.sub(r"([A-Za-zÀ-ỹ])(\d)", r"\1 \2", text)

    return text.strip()


# ==========================================================
# MAIN CHUNK FUNCTION
# ==========================================================

def chunk_text(
    text: str,
    chunk_size: int = 600,
    chunk_overlap: int = 100,
    min_chunk_tokens: int = 50,
) -> List[str]:
    """
    Split text into chunks suitable for embedding & RAG.

    Parameters
    ----------
    text : str
        Input text
    chunk_size : int
        Max tokens (word-estimated) per chunk
    chunk_overlap : int
        Token overlap between chunks
    min_chunk_tokens : int
        Min tokens to accept a chunk

    Returns
    -------
    List[str]
        List of text chunks
    """

    # ------------------------------------------------------
    # 1️⃣ Normalize
    # ------------------------------------------------------

    text = _normalize_text(text)

    if not text:
        return []

    words = text.split()
    total_words = len(words)

    # If shorter than chunk_size → return single chunk
    if total_words <= chunk_size:
        if total_words >= min_chunk_tokens:
            return [text]
        else:
            return []

    # ------------------------------------------------------
    # 2️⃣ Sliding Window Chunking
    # ------------------------------------------------------

    chunks = []
    start = 0
    step = chunk_size - chunk_overlap

    while start < total_words:
        end = min(start + chunk_size, total_words)

        chunk_words = words[start:end]
        token_count = len(chunk_words)

        if token_count >= min_chunk_tokens:
            chunk = " ".join(chunk_words).strip()
            chunks.append(chunk)

        start += step

    return chunks

# afternoon 24/2/2026 =============================
# import re
# from typing import List


# # ==============================
# # CONFIG
# # ==============================

# MIN_CHUNK_LENGTH = 80  # safer than 50


# # ==============================
# # HEADING DETECTION
# # ==============================

# HEADING_PATTERN = re.compile(
#     r"""
#     (
#         ^\s*(?:\d+[\.\)]\s+)              # 1.  2)
#         |
#         ^\s*(?:[IVXLC]+\.)\s+             # I. II.
#         |
#         ^\s*(?:[A-Z][A-Z\s]{5,})$         # HEADING ALL CAPS
#         |
#         ^\s*(?:Cutoff|Tuition|Admission method|Target|Aspiration|Quota)
#     )
#     """,
#     re.IGNORECASE | re.MULTILINE | re.VERBOSE,
# )


# # ==============================
# # SPLIT BY HEADING
# # ==============================

# def split_by_heading(text: str) -> List[str]:
#     matches = list(HEADING_PATTERN.finditer(text))

#     if not matches:
#         return [text]

#     sections = []
#     for i, match in enumerate(matches):
#         start = match.start()
#         end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
#         section = text[start:end].strip()

#         # Skip too-short section (standalone heading)
#         if len(section) > 30:
#             sections.append(section)

#     return sections if sections else [text]


# # ==============================
# # SENTENCE FILTER
# # ==============================

# def is_trivial_sentence(text: str) -> bool:
#     text = text.strip()

#     # numeral like "5." or "3)"
#     if re.fullmatch(r"\d+[\.\)]?", text):
#         return True

#     # too short
#     if len(text) < 20:
#         return True

#     return False


# # ==============================
# # CHUNK FILTER (CRITICAL)
# # ==============================

# def is_bad_chunk(text: str) -> bool:
#     text = text.strip()

#     # Too short
#     if len(text) < MIN_CHUNK_LENGTH:
#         return True

#     # All uppercase (heading)
#     if text.isupper():
#         return True

#     # No sentence-ending punctuation
#     if not any(p in text for p in [".", ":", ";", "?"]):
#         return True

#     # Too few real words
#     if len(text.split()) < 10:
#         return True

#     return False


# # ==============================
# # SECTION CHUNKING
# # ==============================

# def chunk_section(
#     text: str,
#     chunk_size: int = 600,
#     chunk_overlap: int = 100,
# ) -> List[str]:

#     sentences = re.split(r'(?<=[.!?])\s+', text)

#     # Merge trivial sentence with next sentence
#     merged_sentences = []
#     i = 0
#     while i < len(sentences):
#         current = sentences[i].strip()

#         if is_trivial_sentence(current) and i + 1 < len(sentences):
#             current = current + " " + sentences[i + 1]
#             i += 1

#         merged_sentences.append(current)
#         i += 1

#     chunks = []
#     current_chunk = ""

#     for sentence in merged_sentences:
#         if len(current_chunk) + len(sentence) <= chunk_size:
#             current_chunk += " " + sentence
#         else:
#             clean_chunk = current_chunk.strip()

#             if not is_bad_chunk(clean_chunk):
#                 chunks.append(clean_chunk)

#             # overlap
#             current_chunk = current_chunk[-chunk_overlap:] + " " + sentence

#     # Add last chunk
#     clean_chunk = current_chunk.strip()
#     if not is_bad_chunk(clean_chunk):
#         chunks.append(clean_chunk)

#     return chunks


# # ==============================
# # MAIN ENTRY
# # ==============================

# def chunk_text(
#     text: str,
#     chunk_size: int = 600,
#     chunk_overlap: int = 100,
# ) -> List[str]:

#     if not text:
#         return []

#     sections = split_by_heading(text)

#     all_chunks = []

#     for section in sections:
#         section_chunks = chunk_section(
#             section,
#             chunk_size=chunk_size,
#             chunk_overlap=chunk_overlap,
#         )
#         all_chunks.extend(section_chunks)

#     return all_chunks


# legacy before 24/2/2026 ===============================
# from typing import List

# def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
#     """
#     Split text into chunks of chunk_size length
#     with chunk_overlap for context preservation.
#     """
#     if not text or chunk_size <= 0:
#         return []

#     chunks = []
#     start = 0
#     text_len = len(text)

#     while start < text_len:
#         # Take a text segment
#         end = start + chunk_size
#         chunk = text[start:end]
#         chunks.append(chunk)
        
#         # Advance start point (minus overlap)
#         start += (chunk_size - chunk_overlap)
        
#         # Avoid infinite loop if overlap too large
#         if chunk_size <= chunk_overlap:
#             break

#     return chunks