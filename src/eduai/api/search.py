from fastapi import APIRouter, Depends
from typing import List

from sentence_transformers import SentenceTransformer

from eduai.api.schemas import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResult,
)
from eduai.api.deps import (
    get_qdrant_client,
    get_embedding_model,
    COLLECTION_NAME,
)
from eduai.common.jsonio import read_json
from eduai.config.paths import PROCESSED_PATH


router = APIRouter(prefix="/search", tags=["semantic-search"])


@router.post("/semantic", response_model=SemanticSearchResponse)
def semantic_search(
    req: SemanticSearchRequest,
    qdrant=Depends(get_qdrant_client),
    model: SentenceTransformer = Depends(get_embedding_model),
):
    # ---------- Embed query ----------
    query_vector = model.encode(
        req.query,
        normalize_embeddings=True,
    ).tolist()

    # ---------- Search Qdrant ----------
    hits = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=req.top_k,
    )

    results: List[SemanticSearchResult] = []

    for hit in hits:
        payload = hit.payload or {}

        file_hash = payload.get("file_hash")
        chunk_id = payload.get("chunk_id")
        section_id = payload.get("section_id")
        token_estimate = payload.get("token_estimate")

        if not file_hash or not chunk_id:
            continue

        # ---------- Load text from 300_processed ----------
        chunks_file = (
            PROCESSED_PATH / file_hash / "chunks.json"
        )

        if not chunks_file.exists():
            continue

        chunks = read_json(chunks_file)
        chunk_text = None

        for c in chunks:
            if c.get("chunk_id") == chunk_id:
                chunk_text = c.get("text")
                break

        if not chunk_text:
            continue

        results.append(
            SemanticSearchResult(
                score=hit.score,
                file_hash=file_hash,
                chunk_id=chunk_id,
                section_id=section_id,
                text=chunk_text,
                token_estimate=token_estimate,
            )
        )

    return SemanticSearchResponse(
        query=req.query,
        results=results,
    )
