"""
Admission Agent - API compatible with Research Agent: /metadata, /data, /ask.
Uses Qwen3 8b, data from collection "Admission" in Qdrant.
"""

import time
import requests
from fastapi import APIRouter, HTTPException, Query

from lakeflow.i18n import i18n_detail
from pydantic import BaseModel, Field

from lakeflow.common.text_normalizer import canonicalize_text
from lakeflow.core.config import get_qdrant_url, LLM_MODEL
from lakeflow.services.ollama_embed_service import embed_batch
from lakeflow.services.llm_chat_service import chat_completion
from lakeflow.services.qdrant_service import get_client

ADMISSION_COLLECTION = "Admission"

router = APIRouter(
    prefix="/admission_agent/v1",
    tags=["admission-agent"],
)


class AskRequest(BaseModel):
    session_id: str | None = None
    model_id: str | None = None
    user: str | None = None
    prompt: str = Field(..., description="User's question")
    context: dict | None = None


@router.get("/metadata")
def get_metadata() -> dict:
    """
    Admission Agent metadata (compatible with Research agent).
    """
    return {
        "name": "Admission Information",
        "description": "Answer questions about admissions, enrollment regulations, and related documents. Data from Admission collection in Qdrant.",
        "version": "1.0.0",
        "developer": "LakeFlow",
        "capabilities": ["admission", "enrollment", "regulations", "documents"],
        "supported_models": [
            {
                "model_id": "qwen3:8b",
                "name": "Qwen3 8B",
                "description": "Ollama model for Q&A based on Admission documents",
                "accepted_file_types": [],
            },
        ],
        "sample_prompts": [
            "What is the total regular university enrollment quota for 2026?",
            "What are the new CTTA programs in 2026 enrollment?",
            "What is the AI enrollment quota for 2026?",
            "List of high-quality (CLC) programs for 2026 enrollment?",
        ],
        "provided_data_types": [
            {"type": "qdrant_collection", "description": "Admission collection in Qdrant"},
        ],
        "contact": "",
        "status": "active",
    }


def _collect_sources_from_collection(collection: str, limit: int = 500) -> list[dict]:
    """Scroll collection, collect unique sources from payload."""
    sources_seen: set[str] = set()
    sources: list[dict] = []
    client = get_client(None)
    offset = None

    while len(sources) < limit:
        points, offset = client.scroll(
            collection_name=collection,
            limit=min(100, limit - len(sources)),
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        if not points:
            break
        for p in points:
            payload = p.payload or {}
            source = payload.get("source") or payload.get("file_hash") or ""
            if source and source not in sources_seen:
                sources_seen.add(source)
                sources.append({
                    "source": source,
                    "file_hash": payload.get("file_hash"),
                    "chunk_id": payload.get("chunk_id"),
                })
                if len(sources) >= limit:
                    break
        if offset is None:
            break

    return sources


@router.get("/data")
def get_data(limit: int = Query(100, ge=1, le=500)):
    """
    List of data sources from Admission collection.
    """
    try:
        client = get_client(None)
        client.get_collection(ADMISSION_COLLECTION)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=i18n_detail(
                "admission.collection_not_exist",
                collection=ADMISSION_COLLECTION,
                error=str(e),
            ),
        )
    sources = _collect_sources_from_collection(ADMISSION_COLLECTION, limit=limit)
    return {"sources": sources, "count": len(sources)}


@router.post("/ask")
def ask(req: AskRequest):
    """
    RAG: Find context from semantic search on Admission collection, call LLM to answer.
    """
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail=i18n_detail("admission.prompt_empty"))

    # 1. Embed query (using Ollama qwen3-embedding - matches Admission collection)
    expanded = canonicalize_text(prompt)
    query_vector = embed_batch([expanded])[0]

    # 2. Search Qdrant
    base = get_qdrant_url(None)
    url = f"{base}/collections/{ADMISSION_COLLECTION}/points/search"
    payload = {
        "vector": query_vector,
        "limit": 8,
        "with_payload": True,
        "with_vector": False,
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail=i18n_detail("admission.qdrant_search_failed", error=str(exc)),
        )

    data = resp.json()
    points = data.get("result", [])

    if not points:
        return {
            "session_id": req.session_id,
            "status": "success",
            "content_markdown": "According to the provided documents, there is no information to answer this question.",
            "meta": {"model": LLM_MODEL},
            "attachments": [],
        }

    context_texts = []
    contexts = []
    for p in points:
        pl = p.get("payload", {}) or {}
        text = pl.get("text", "")
        if text:
            context_texts.append(text)
        contexts.append({
            "id": p.get("id"),
            "score": float(p.get("score", 0)),
            "file_hash": pl.get("file_hash"),
            "chunk_id": pl.get("chunk_id"),
            "text": text,
        })

    context_block = "\n\n".join(
        f"[Context {i+1}]:\n{t}" for i, t in enumerate(context_texts)
    )

    system_prompt = """Ban dang tham gia mot demo RAG (Retrieval-Augmented Generation). Nhiem vu cua ban la tra loi cau hoi CHI dua tren cac doan tai lieu (context) duoc cung cap ben duoi.

QUY TAC BAT BUOC:
- Chi duoc tra loi dua tren noi dung trong context. Khong dung kien thuc ben ngoai, khong suy doan them.
- Neu cau tra loi co trong context: trich dan hoac tom tat tu context mot cach chinh xac, tra loi bang tieng Viet.
- Neu context khong chua thong tin de tra loi cau hoi: hay noi ro "Theo cac tai lieu duoc cung cap, khong co thong tin de tra loi cau hoi nay." va khong bia dap an.
- Tra loi ngan gon, ro rang, bang tieng Viet."""

    user_prompt = f"""Cac doan tai lieu (context) dung de tra loi - CHI dua vao day:

{context_block}

---
Cau hoi: {prompt}

Tra loi (chi dua tren context tren):"""

    t0 = time.time()
    try:
        answer, model_used = chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=500,
            detail=i18n_detail("admission.llm_api_failed", error=str(exc)),
        )
    except (KeyError, IndexError) as exc:
        raise HTTPException(
            status_code=500,
            detail=i18n_detail("admission.invalid_llm_response", error=str(exc)),
        )

    response_time_ms = int((time.time() - t0) * 1000)
    tokens_used = None

    # Format compatible with Research Chat: content_markdown only
    return {
        "session_id": req.session_id,
        "status": "success",
        "content_markdown": answer,
        "meta": {
            "model": model_used,
            "response_time_ms": response_time_ms,
            "tokens_used": tokens_used,
        },
        "attachments": [],
    }
