from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import json

import numpy as np
from sentence_transformers import SentenceTransformer

from eduai.common.jsonio import read_json, write_json


DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def run_embedding_pipeline(
    file_hash: str,
    processed_dir: Path,
    embeddings_root: Path,
    model_name: str = DEFAULT_MODEL_NAME,
    force: bool = False,
) -> None:
    """
    Sinh embedding từ 300_processed → 400_embeddings
    """

    chunks_file = processed_dir / "chunks.json"
    if not chunks_file.exists():
        raise RuntimeError(f"Missing chunks.json for {file_hash}")

    out_dir = embeddings_root / file_hash

    if out_dir.exists() and not force:
        print(f"[400] Skip (already embedded): {file_hash}")
        return

    out_dir.mkdir(parents=True, exist_ok=True)

    # ---------- Load chunks ----------
    chunks: List[Dict[str, Any]] = read_json(chunks_file)
    texts = [c["text"] for c in chunks]

    if not texts:
        print(f"[400] No text chunks for {file_hash}, skip")
        return

    # ---------- Load model ----------
    print(f"[400] Loading model: {model_name}")
    model = SentenceTransformer(model_name)

    # ---------- Generate embeddings ----------
    print(f"[400] Embedding {len(texts)} chunks")
    vectors = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    vectors = np.asarray(vectors, dtype="float32")

    # ---------- Save embeddings ----------
    np.save(out_dir / "embeddings.npy", vectors)

    # ---------- Save chunk metadata ----------
    chunks_meta = [
        {
            "chunk_id": c["chunk_id"],
            "section_id": c.get("section_id"),
            "file_hash": file_hash,
            "token_estimate": c.get("token_estimate"),
        }
        for c in chunks
    ]

    write_json(out_dir / "chunks_meta.json", chunks_meta)

    # ---------- Save model metadata ----------
    model_info = {
        "model_name": model_name,
        "embedding_dim": int(vectors.shape[1]),
        "chunk_count": len(vectors),
        "created_at": datetime.utcnow().isoformat(),
        "source": "300_processed",
    }

    write_json(out_dir / "model.json", model_info)

    # ---------- Optional: JSONL for debug ----------
    with (out_dir / "embeddings.jsonl").open("w", encoding="utf-8") as f:
        for meta, vec in zip(chunks_meta, vectors):
            record = {
                **meta,
                "vector": vec.tolist(),
            }
            f.write(json.dumps(record) + "\n")

    print(f"[400] Completed embeddings for {file_hash}")
