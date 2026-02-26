# file này thực hiện:
#   - Load model embedding
#   - Tạo vector
#   - Lưu embedding.npy
# ==========================================================
from pathlib import Path
from typing import Literal, Optional

import numpy as np

from lakeflow.common.jsonio import write_json
from lakeflow.common.nas_io import nas_safe_mkdir, nas_safe_read_json
from lakeflow.services.ollama_embed_service import embed_batch
from lakeflow.common.text_normalizer import canonicalize_text

EmbeddingStatus = Literal["EMBEDDED", "SKIPPED"]


def run_embedding_pipeline(
    file_hash: str,
    processed_dir: Path,
    embeddings_root: Path,
    force: bool = False,
    parent_dir: Optional[str] = None,
) -> EmbeddingStatus:
    """
    parent_dir: thư mục cha (domain) — output sẽ là 400_embeddings/<parent_dir>/<file_hash>/
    Nếu không truyền: 400_embeddings/<file_hash>/ (giữ tương thích).
    """

    # =====================================================
    # 1. Validate input
    # =====================================================
    chunks_file = processed_dir / "chunks.json"
    if not chunks_file.exists():
        raise RuntimeError(f"Missing chunks.json for {file_hash}")

    if parent_dir:
        out_dir = embeddings_root / parent_dir / file_hash
    else:
        out_dir = embeddings_root / file_hash
    final_path = out_dir / "embedding.npy"

    if final_path.exists() and not force:
        print(f"[400] Skip (already embedded): {file_hash}")
        return "SKIPPED"

    # =====================================================
    # 2. Load chunks (đọc từ NAS với retry)
    # =====================================================
    chunks = nas_safe_read_json(chunks_file)
    texts = [c["text"].strip() for c in chunks if c.get("text")]

    if not texts:
        print(f"[400] No valid text chunks for {file_hash}, skip")
        return "SKIPPED"

    # # =====================================================
    # # 3. Load model & embed
    # # =====================================================
    # print(f"[400] Loading model: {model_name}")
    # model = SentenceTransformer(model_name)

    # print(f"[400] Embedding {len(texts)} chunks for {file_hash}")
    # vectors = model.encode(
    #     texts,
    #     show_progress_bar=True,
    #     normalize_embeddings=True,
    # ).astype("float32")
    
    # =====================================================
    # 3. Embed via Ollama (Qwen3 4096-dim)
    # =====================================================
    print(f"[400] Embedding {len(texts)} chunks via Ollama for {file_hash}")

    BATCH_SIZE = 16
    all_vectors = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i+BATCH_SIZE] 
        normalized_chunks = [canonicalize_text(c) for c in batch]
        batch_vectors = embed_batch(normalized_chunks)
        all_vectors.extend(batch_vectors)

    vectors = np.array(all_vectors, dtype="float32")

    chunks_meta = [
        {
            "chunk_id": c.get("chunk_id"),
            "section_id": c.get("section_id"),
            "file_hash": file_hash,
            "token_estimate": c.get("token_estimate"),
        }
        for c in chunks
    ]

    nas_safe_mkdir(out_dir)
    np.save(final_path, vectors)
    write_json(out_dir / "chunks_meta.json", chunks_meta)

    print(f"[400] Completed embedding for {file_hash}")
    return "EMBEDDED"
