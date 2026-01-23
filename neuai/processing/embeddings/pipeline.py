from pathlib import Path
from typing import Dict, Any, List, Literal
from datetime import datetime
import json

import numpy as np
from sentence_transformers import SentenceTransformer

from neuai.common.jsonio import read_json, write_json


EmbeddingStatus = Literal["EMBEDDED", "SKIPPED"]


DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def run_embedding_pipeline(
    file_hash: str,
    processed_dir: Path,
    embeddings_root: Path,
    model_name: str = DEFAULT_MODEL_NAME,
    force: bool = False,
) -> EmbeddingStatus:
    """
    Sinh embedding từ 300_processed → 400_embeddings.

    Parameters
    ----------
    file_hash : str
        Định danh file (hash)
    processed_dir : Path
        Thư mục 300_processed/<file_hash>
    embeddings_root : Path
        Root của 400_embeddings
    model_name : str
        Tên model sentence-transformers
    force : bool
        True để regenerate embeddings

    Returns
    -------
    EmbeddingStatus
        "EMBEDDED" | "SKIPPED"
    """

    # ---------- 1. Validate input ----------
    chunks_file = processed_dir / "chunks.json"
    if not chunks_file.exists():
        raise RuntimeError(
            f"Missing chunks.json for file_hash={file_hash}"
        )

    # ---------- 2. Prepare output directory ----------
    out_dir = embeddings_root / file_hash

    if out_dir.exists() and not force:
        # Đã có embedding → skip
        print(f"[400] Skip (already embedded): {file_hash}")
        return "SKIPPED"

    out_dir.mkdir(parents=True, exist_ok=True)

    # ---------- 3. Load chunks ----------
    chunks: List[Dict[str, Any]] = read_json(chunks_file)

    texts = [c.get("text", "").strip() for c in chunks if c.get("text")]
    if not texts:
        print(f"[400] No valid text chunks for {file_hash}, skip")
        return "SKIPPED"

    # ---------- 4. Load embedding model ----------
    print(f"[400] Loading model: {model_name}")
    model = SentenceTransformer(model_name)

    # ---------- 5. Generate embeddings ----------
    print(f"[400] Embedding {len(texts)} chunks for {file_hash}")
    vectors = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    vectors = np.asarray(vectors, dtype="float32")

    # ---------- 6. Save embeddings.npy ----------
    np.save(out_dir / "embeddings.npy", vectors)

    # ---------- 7. Save chunks metadata ----------
    chunks_meta = [
        {
            "chunk_id": c.get("chunk_id"),
            "section_id": c.get("section_id"),
            "file_hash": file_hash,
            "token_estimate": c.get("token_estimate"),
        }
        for c in chunks
    ]

    write_json(out_dir / "chunks_meta.json", chunks_meta)

    # ---------- 8. Save model metadata ----------
    model_info = {
        "model_name": model_name,
        "embedding_dim": int(vectors.shape[1]),
        "chunk_count": len(vectors),
        "created_at": datetime.utcnow().isoformat(),
        "source_zone": "300_processed",
        "pipeline": "400_embeddings",
    }

    write_json(out_dir / "model.json", model_info)

    # ---------- 9. Optional: embeddings.jsonl (debug / audit) ----------
    with (out_dir / "embeddings.jsonl").open("w", encoding="utf-8") as f:
        for meta, vec in zip(chunks_meta, vectors):
            record = {
                **meta,
                "vector": vec.tolist(),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"[400] Completed embeddings for {file_hash}")
    return "EMBEDDED"
