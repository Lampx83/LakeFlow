"""
Library Regulation Agent (Quy định hướng dẫn) - API compatible with Research Agent: /metadata, /data, /ask.
Uses Qwen3 8b, data from collection "Library_TCTL" in Qdrant (Word: quy định, hướng dẫn thư viện).
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

LIBRARY_REGULATION_COLLECTION = "Library_TCTL"

router = APIRouter(
    prefix="/library_regulation_agent/v1",
    tags=["library-regulation-agent"],
)


class AskRequest(BaseModel):
    session_id: str | None = None
    model_id: str | None = None
    user: str | None = None
    prompt: str = Field(..., description="Câu hỏi của người dùng")
    context: dict | None = None


@router.get("/metadata")
def get_metadata() -> dict:
    """
    Metadata trợ lý Quy định hướng dẫn.
    """
    return {
        "name": "Quy định hướng dẫn",
        "description": "Tra cứu thông tin trong các file Word: giới thiệu chung, hướng dẫn nộp chuyên đề tốt nghiệp thạc sĩ, hướng dẫn tìm kiếm và khai thác thông tin, tài liệu hướng dẫn thư viện. Dữ liệu từ bộ sưu tập Library_TCTL trong Qdrant.",
        "version": "1.0.0",
        "developer": "LakeFlow",
        "primary_language": "vi",
        "capabilities": ["thư viện", "quy định", "hướng dẫn", "word", "luận văn", "tìm kiếm"],
        "supported_models": [
            {
                "model_id": "qwen3:8b",
                "name": "Qwen3 8B",
                "description": "Mô hình Ollama hỏi đáp dựa trên tài liệu quy định hướng dẫn (Word)",
                "accepted_file_types": [],
            },
        ],
        "sample_prompts": [
            "Hướng dẫn nộp chuyên đề tốt nghiệp thạc sĩ như thế nào?",
            "Cách tìm kiếm và khai thác thông tin thư viện?",
            "Quy định về nộp luận văn?",
            "Tài liệu hướng dẫn sử dụng thư viện có những nội dung gì?",
        ],
        "provided_data_types": [
            {"type": "qdrant_collection", "description": "Bộ sưu tập Library_TCTL trong Qdrant (nguồn Word)"},
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
    Danh sách nguồn dữ liệu từ bộ sưu tập Library_TCTL.
    """
    try:
        client = get_client(None)
        client.get_collection(LIBRARY_REGULATION_COLLECTION)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=i18n_detail(
                "library_regulation.collection_not_exist",
                collection=LIBRARY_REGULATION_COLLECTION,
                error=str(e),
            ),
        )
    sources = _collect_sources_from_collection(LIBRARY_REGULATION_COLLECTION, limit=limit)
    return {"sources": sources, "count": len(sources)}


@router.post("/ask")
def ask(req: AskRequest):
    """
    RAG: Lấy đoạn tài liệu liên quan từ bộ sưu tập Library_TCTL, gọi LLM trả lời.
    """
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail=i18n_detail("library_regulation.prompt_empty"))

    # 1. Embed query
    expanded = canonicalize_text(prompt)
    query_vector = embed_batch([expanded])[0]

    # 2. Search Qdrant
    base = get_qdrant_url(None)
    url = f"{base}/collections/{LIBRARY_REGULATION_COLLECTION}/points/search"
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
            detail=i18n_detail("library_regulation.qdrant_search_failed", error=str(exc)),
        )

    data = resp.json()
    points = data.get("result", [])

    if not points:
        return {
            "session_id": req.session_id,
            "status": "success",
            "content_markdown": "Theo các tài liệu được cung cấp, không có thông tin để trả lời câu hỏi này.",
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
        f"[Đoạn {i+1}]:\n{t}" for i, t in enumerate(context_texts)
    )

    system_prompt = """Bạn đang tham gia một demo RAG (Quy định hướng dẫn thư viện). Nhiệm vụ của bạn là trả lời câu hỏi CHỈ dựa trên các đoạn tài liệu được cung cấp bên dưới.

QUY TẮC BẮT BUỘC:
- Chỉ được trả lời dựa trên nội dung trong các đoạn tài liệu đó. Không dùng kiến thức bên ngoài, không suy đoán thêm.
- Nếu câu trả lời có trong tài liệu: trích dẫn hoặc tóm tắt từ tài liệu một cách chính xác, trả lời bằng tiếng Việt.
- Nếu tài liệu không chứa thông tin để trả lời câu hỏi: hãy nói rõ "Theo các tài liệu được cung cấp, không có thông tin để trả lời câu hỏi này." và không bịa đáp án.
- Trả lời ngắn gọn, rõ ràng, bằng tiếng Việt."""

    user_prompt = f"""Các đoạn tài liệu dùng để trả lời - CHỈ dựa vào đây:

{context_block}

---
Câu hỏi: {prompt}

Trả lời (chỉ dựa trên tài liệu trên):"""

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
            detail=i18n_detail("library_regulation.llm_api_failed", error=str(exc)),
        )
    except (KeyError, IndexError) as exc:
        raise HTTPException(
            status_code=500,
            detail=i18n_detail("library_regulation.invalid_llm_response", error=str(exc)),
        )

    response_time_ms = int((time.time() - t0) * 1000)
    tokens_used = None

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
