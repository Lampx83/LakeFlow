"""
Research KHCN Regulation Agent — quy chế, quy trình Khoa học công nghệ (Phụ lục 1–11).
API tương thích Research Agent: /metadata, /data, /ask.
RAG trên collection Qdrant research_regulations_and_policies (quy định, chính sách KHCN).
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

RESEARCH_KHCN_COLLECTION = "research_regulation"

router = APIRouter(
    prefix="/research_khcn_regulation_agent/v1",
    tags=["research-khcn-regulation-agent"],
)


class AskRequest(BaseModel):
    session_id: str | None = None
    model_id: str | None = None
    user: str | None = None
    prompt: str = Field(..., description="Câu hỏi của người dùng")
    context: dict | None = None


@router.get("/metadata")
def get_metadata() -> dict:
    return {
        "name": "Quy chế Khoa học công nghệ",
        "description": (
            "Trợ lý tra cứu quy chế, quy trình, biểu mẫu và hướng dẫn về Khoa học công nghệ "
            "(Phụ lục 1–11: đề tài các cấp, nhóm công bố, thẩm định giáo trình/sách, hội thảo, "
            "giải thưởng SV NCKH, giờ NCKH, sinh hoạt khoa học bộ môn, CBQT/HTQT). "
            f"Dữ liệu RAG từ bộ sưu tập {RESEARCH_KHCN_COLLECTION} trong Qdrant."
        ),
        "version": "1.0.0",
        "developer": "LakeFlow",
        "primary_language": "vi",
        "capabilities": [
            "khoa học công nghệ",
            "quy chế",
            "quy trình",
            "biểu mẫu",
            "đề tài",
            "NCKH",
            "công bố quốc tế",
            "hội thảo",
            "phụ lục",
        ],
        "supported_models": [
            {
                "model_id": "qwen3:8b",
                "name": "Qwen3 8B",
                "description": "Mô hình Ollama hỏi đáp dựa trên tài liệu quy chế KHCN",
                "accepted_file_types": [],
            },
        ],
        "sample_prompts": [
            "Phụ lục 1: Quy trình và văn bản pháp lý cho đề tài cấp Nhà nước, cấp Bộ gồm những bước nào?",
            "Đề tài cấp Trường (Phụ lục 2) cần nộp những biểu mẫu gì và theo thứ tự nào?",
            "Nhóm công bố quốc tế (Phụ lục 3): điều kiện thành lập và quy trình hoạt động ra sao?",
            "Phụ lục 4: Quy trình và biểu mẫu cho nhóm nghiên cứu định hướng truyền thông?",
            "Thẩm định giáo trình (Phụ lục 5) có những bước và hồ sơ bắt buộc nào?",
            "Thẩm định sách phục vụ đào tạo (Phụ lục 6) khác gì so với thẩm định giáo trình?",
            "Tổ chức hội thảo, tọa đàm khoa học (Phụ lục 7): quy trình xin phép và quản lý?",
            "Giải thưởng Sinh viên NCKH cấp Trường (Phụ lục 8): các biểu mẫu và điều kiện xét?",
            "Kê khai giờ NCKH và định mức giờ NCKH (Phụ lục 9) được quy định thế nào?",
            "Sinh hoạt khoa học bộ môn (Phụ lục 10): tần suất, nội dung và biểu mẫu ghi nhận?",
            "Kê khai công bố quốc tế (CBQT) và tham dự hội thảo quốc tế (HTQT) theo Phụ lục 11?",
            "Tóm tắt các phụ lục trong bộ Quy chế — Chính sách và quy định KHCN?",
        ],
        "provided_data_types": [
            {
                "type": "qdrant_collection",
                "description": (
                    f"Bộ sưu tập {RESEARCH_KHCN_COLLECTION} — ingest tài liệu từ thư mục "
                    "\"Regulations and Policies\" / các Phụ lục 1–11 (PDF, Word) qua pipeline LakeFlow."
                ),
            },
        ],
        "contact": "",
        "status": "active",
    }


def _collect_sources_from_collection(collection: str, limit: int = 500) -> list[dict]:
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
    try:
        client = get_client(None)
        client.get_collection(RESEARCH_KHCN_COLLECTION)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=i18n_detail(
                "khcn_regulation.collection_not_exist",
                collection=RESEARCH_KHCN_COLLECTION,
                error=str(e),
            ),
        )
    sources = _collect_sources_from_collection(RESEARCH_KHCN_COLLECTION, limit=limit)
    return {"sources": sources, "count": len(sources)}


@router.post("/ask")
def ask(req: AskRequest):
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail=i18n_detail("khcn_regulation.prompt_empty"))

    expanded = canonicalize_text(prompt)
    query_vector = embed_batch([expanded])[0]

    base = get_qdrant_url(None)
    url = f"{base}/collections/{RESEARCH_KHCN_COLLECTION}/points/search"
    payload = {
        "vector": query_vector,
        "limit": 10,
        "with_payload": True,
        "with_vector": False,
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail=i18n_detail("khcn_regulation.qdrant_search_failed", error=str(exc)),
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
    for p in points:
        pl = p.get("payload", {}) or {}
        text = pl.get("text", "")
        if text:
            context_texts.append(text)

    context_block = "\n\n".join(
        f"[Đoạn {i+1}]:\n{t}" for i, t in enumerate(context_texts)
    )

    system_prompt = """Bạn là trợ lý tra cứu quy chế và quy trình Khoa học công nghệ (KHCN) tại cơ sở giáo dục đại học. Tài liệu nguồn gồm các phụ lục về: đề tài cấp Nhà nước/Bộ/Trường; nhóm công bố quốc tế; nhóm nghiên cứu truyền thông; thẩm định giáo trình và sách đào tạo; hội thảo/tọa đàm; giải thưởng SV NCKH; kê khai giờ NCKH; sinh hoạt khoa học bộ môn; kê khai CBQT và tham dự HTQT.

QUY TẮC BẮT BUỘC:
- Chỉ trả lời dựa trên các đoạn tài liệu được cung cấp. Không bịa quy định, không dùng kiến thức bên ngoài khi mâu thuẫn với tài liệu.
- Trích dẫn hoặc tóm tắt chính xác; ưu tiên nêu rõ quy trình, biểu mẫu, thời hạn, thẩm quyền nếu có trong tài liệu.
- Nếu tài liệu không đủ: nói rõ "Theo các tài liệu được cung cấp, không có thông tin để trả lời câu hỏi này."
- Trả lời bằng tiếng Việt, súc tích, có thể dùng gạch đầu dòng khi liệt kê bước hoặc hồ sơ."""

    user_prompt = f"""Các đoạn tài liệu — CHỈ dựa vào đây:

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
            max_tokens=1200,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=500,
            detail=i18n_detail("khcn_regulation.llm_api_failed", error=str(exc)),
        )
    except (KeyError, IndexError) as exc:
        raise HTTPException(
            status_code=500,
            detail=i18n_detail("khcn_regulation.invalid_llm_response", error=str(exc)),
        )

    response_time_ms = int((time.time() - t0) * 1000)

    return {
        "session_id": req.session_id,
        "status": "success",
        "content_markdown": answer,
        "meta": {
            "model": model_used,
            "response_time_ms": response_time_ms,
            "tokens_used": None,
        },
        "attachments": [],
    }
