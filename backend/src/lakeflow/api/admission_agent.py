"""
Tro ly (Agent) Admission - API tuong thich Research Agent: /metadata, /data, /ask.
Su dung Qwen3 8b, du lieu tu collection "Admission" trong Qdrant.
"""

import time
import requests
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from lakeflow.common.text_normalizer import canonicalize_text
from lakeflow.core.config import get_qdrant_url
from lakeflow.services.ollama_embed_service import embed_batch
from lakeflow.services.llm_chat_service import chat_completion
from lakeflow.services.qdrant_service import get_client

ADMISSION_COLLECTION = "Admission"

router = APIRouter(
    prefix="/admission_agent/v1",
    tags=["admission-agent"],
)


# ---------------------------------------------------------------------------
# Schemas (tuong thich Research agent)
# ---------------------------------------------------------------------------

class AskRequest(BaseModel):
    session_id: str | None = None
    model_id: str | None = None
    user: str | None = None
    prompt: str = Field(..., description="Cau hoi cua nguoi dung")
    context: dict | None = None


# ---------------------------------------------------------------------------
# GET /metadata
# ---------------------------------------------------------------------------

@router.get("/metadata")
def get_metadata() -> dict:
    """
    Metadata cua Tro ly Admission (tuong thich Research agent).
    """
    return {
        "name": "Thông tin tuyển sinh",
        "description": "Tra loi cau hoi ve tuyen sinh, quy che tuyen sinh va tai lieu lien quan. Du lieu lay tu collection Admission trong Qdrant.",
        "version": "1.0.0",
        "developer": "LakeFlow",
        "capabilities": ["admission", "tuyen sinh", "quy che", "tai lieu"],
        "supported_models": [
            {
                "model_id": "qwen3:8b",
                "name": "Qwen3 8B",
                "description": "Mo hinh Ollama cho hoi dap dua tren tai lieu Admission",
                "accepted_file_types": [],
            },
        ],
        "sample_prompts": [
            "Tổng chỉ tiêu tuyển sinh đại học chính quy năm 2026 là bao nhiêu?",
            "Các ngành đào tạo mới (CTTA) trong tuyển sinh 2026?",
            "Ngành Trí tuệ nhân tạo có chỉ tiêu tuyển sinh năm 2026 là bao nhiêu?",
            "Danh sách các chương trình chất lượng cao (CLC) tuyển sinh 2026?",
        ],
        "provided_data_types": [
            {"type": "qdrant_collection", "description": "Collection Admission trong Qdrant"},
        ],
        "contact": "",
        "status": "active",
    }


# ---------------------------------------------------------------------------
# GET /data - danh sach nguon du lieu (tu collection Admission)
# ---------------------------------------------------------------------------

def _collect_sources_from_collection(collection: str, limit: int = 500) -> list[dict]:
    """Scroll collection, thu thap cac nguon (source) duy nhat tu payload."""
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
    Danh sach nguon du lieu tu collection Admission.
    """
    try:
        client = get_client(None)
        client.get_collection(ADMISSION_COLLECTION)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Collection {ADMISSION_COLLECTION} khong ton tai hoac Qdrant chua san sang: {e}",
        )
    sources = _collect_sources_from_collection(ADMISSION_COLLECTION, limit=limit)
    return {"sources": sources, "count": len(sources)}


# ---------------------------------------------------------------------------
# POST /ask - RAG hoi dap
# ---------------------------------------------------------------------------

@router.post("/ask")
def ask(req: AskRequest):
    """
    RAG: Tim context tu semantic search tren collection Admission, goi LLM tra loi.
    """
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt khong duoc de trong")

    # 1. Embed query (dùng Ollama qwen3-embedding - khớp với collection Admission)
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
            detail=f"Qdrant search that bai: {exc}",
        )

    data = resp.json()
    points = data.get("result", [])

    if not points:
        return {
            "session_id": req.session_id,
            "status": "success",
            "content_markdown": "Theo cac tai lieu duoc cung cap, khong co thong tin de tra loi cau hoi nay.",
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
            detail=f"LLM API that bai: {exc}",
        )
    except (KeyError, IndexError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Phan hoi LLM khong hop le: {exc}",
        )

    response_time_ms = int((time.time() - t0) * 1000)
    tokens_used = None

    # Format tuong thich Research Chat: chi content_markdown
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
