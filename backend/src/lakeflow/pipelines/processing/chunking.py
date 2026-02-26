"""
Chunking module cho LakeFlow AI ingestion pipeline.

Mục tiêu:
- Semantic-friendly chunking
- Tránh tạo chunk quá nhỏ
- Hỗ trợ overlap để tăng recall trong RAG
- Chuẩn hóa text trước khi chia chunk
"""

import re
from typing import List


# ==========================================================
# TEXT NORMALIZATION
# ==========================================================

def _normalize_text(text: str) -> str:
    """
    Chuẩn hóa văn bản trước khi chunk:
    - Gộp nhiều whitespace
    - Chuẩn hóa newline
    - Fix chữ dính số (VD: tuyển sinh3 → tuyển sinh 3)
    """

    if not text:
        return ""

    # Chuẩn hóa newline
    text = re.sub(r"\r\n", "\n", text)

    # Gộp nhiều khoảng trắng thành 1
    text = re.sub(r"[ \t]+", " ", text)

    # Loại bỏ nhiều newline liên tiếp
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Fix chữ dính số
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
    Chia văn bản thành các chunk phù hợp cho embedding & RAG.

    Parameters
    ----------
    text : str
        Văn bản đầu vào
    chunk_size : int
        Số token (ước lượng theo word) tối đa mỗi chunk
    chunk_overlap : int
        Số token overlap giữa các chunk
    min_chunk_tokens : int
        Số token tối thiểu để chấp nhận một chunk

    Returns
    -------
    List[str]
        Danh sách các chunk văn bản
    """

    # ------------------------------------------------------
    # 1️⃣ Normalize
    # ------------------------------------------------------

    text = _normalize_text(text)

    if not text:
        return []

    words = text.split()
    total_words = len(words)

    # Nếu ngắn hơn chunk_size → trả về 1 chunk duy nhất
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

# chiều 24/2/2026=============================
# import re
# from typing import List


# # ==============================
# # CONFIG
# # ==============================

# MIN_CHUNK_LENGTH = 80  # an toàn hơn 50


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
#         ^\s*(?:Điểm chuẩn|Học phí|Phương thức xét tuyển|Đối tượng|Nguyện vọng|Chỉ tiêu)
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

#         # Loại section quá ngắn (heading standalone)
#         if len(section) > 30:
#             sections.append(section)

#     return sections if sections else [text]


# # ==============================
# # SENTENCE FILTER
# # ==============================

# def is_trivial_sentence(text: str) -> bool:
#     text = text.strip()

#     # chỉ số như "5." hoặc "3)"
#     if re.fullmatch(r"\d+[\.\)]?", text):
#         return True

#     # quá ngắn
#     if len(text) < 20:
#         return True

#     return False


# # ==============================
# # CHUNK FILTER (CRITICAL)
# # ==============================

# def is_bad_chunk(text: str) -> bool:
#     text = text.strip()

#     # Quá ngắn
#     if len(text) < MIN_CHUNK_LENGTH:
#         return True

#     # Toàn chữ in hoa (heading)
#     if text.isupper():
#         return True

#     # Không có dấu kết thúc câu
#     if not any(p in text for p in [".", ":", ";", "?"]):
#         return True

#     # Quá ít từ thực
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

#     # Merge trivial sentence với câu sau
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


# cũ trước 24/2/2026===============================
# from typing import List

# def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
#     """
#     Chia nhỏ văn bản thành các đoạn (chunks) có độ dài chunk_size 
#     và có phần chồng lấn chunk_overlap để giữ ngữ cảnh.
#     """
#     if not text or chunk_size <= 0:
#         return []

#     chunks = []
#     start = 0
#     text_len = len(text)

#     while start < text_len:
#         # Lấy một đoạn văn bản
#         end = start + chunk_size
#         chunk = text[start:end]
#         chunks.append(chunk)
        
#         # Dịch chuyển điểm bắt đầu (trừ đi phần chồng lấn)
#         start += (chunk_size - chunk_overlap)
        
#         # Tránh vòng lặp vô tận nếu overlap quá lớn
#         if chunk_size <= chunk_overlap:
#             break

#     return chunks