"""
Tro ly (Agent) Admission - API tuong thich Research Agent: /metadata, /data, /ask.
Su dung Qwen3 8b, du lieu tu collection "Admission" trong Qdrant.
"""

import time
import requests
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from lakeflow.common.text_normalizer import canonicalize_text
from lakeflow.services.ollama_embed_service import embed_batch
from lakeflow.core.config import get_qdrant_url, LLM_BASE_URL, LLM_MODEL, OPENAI_API_KEY
from lakeflow.services.qdrant_service import get_client


import os
from lakeflow.catalog.db import get_connection
from lakeflow.config.paths import catalog_db_path


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
        "name": "Admission",
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
            "Dieu kien tuyen sinh dai hoc chinh quy la gi?",
            "Thoi gian nop ho so tuyen sinh nam nay?",
            "Cac nganh dao tao va chi tieu tuyen sinh?",
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


# -----------------------------------------------------------
# hàm lấy tên file từ file_hash
#    - tra file_hash -> source_path
#    - lấy basename để ra tên file thật
#    - tạo danh sách sources không bị trùng
# -----------------------------------------------------------
def _resolve_filenames_by_hash(file_hashes: list[str]) -> dict[str, str]:
    hashes = [h for h in file_hashes if h]
    if not hashes:
        return {}

    conn = get_connection(catalog_db_path())
    try:
        placeholders = ",".join("?" for _ in hashes)
        sql = f"""
            SELECT hash, source_path
            FROM ingest_log
            WHERE hash IN ({placeholders})
              AND source_path IS NOT NULL
            ORDER BY id DESC
        """
        rows = conn.execute(sql, hashes).fetchall()

        mapping = {}
        for file_hash, source_path in rows:
            if file_hash and source_path and file_hash not in mapping:
                mapping[file_hash] = os.path.basename(source_path)

        return mapping
    finally:
        conn.close()


def _title_from_filename(filename: str | None) -> str | None:
    if not filename:
        return None

    name = os.path.splitext(filename)[0]
    name = name.replace("-", " ").replace("_", " ")
    name = " ".join(name.split())

    return name


def _build_sources_from_contexts(contexts: list[dict]) -> list[dict]:
    file_hashes = [c.get("file_hash") for c in contexts if c.get("file_hash")]
    filename_map = _resolve_filenames_by_hash(file_hashes)

    sources = []
    seen = set()

    for ctx in contexts:
        file_hash = ctx.get("file_hash")
        filename = filename_map.get(file_hash)

        item = {
            "title": _title_from_filename(filename) or filename or file_hash or "Tài liệu không rõ tên",
            "file": filename,
            "page": None,
        }

        key = (item["title"], item["file"], item["page"])
        if key not in seen:
            seen.add(key)
            sources.append(item)

    return sources

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

    # 1. Embed query
    expanded_query = canonicalize_text(prompt)
    query_vector = embed_batch([expanded_query])[0]

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
            "answer": "Theo cac tai lieu duoc cung cap, khong co thong tin de tra loi cau hoi nay.",
            "contexts": [],
            "model_used": LLM_MODEL,
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

    sources = _build_sources_from_contexts(contexts)

    # --------------------------------------------------
    # 2. Build prompt với context
    # --------------------------------------------------
    context_block = "\n\n".join([
        f"[Context {i+1}]:\n{text}"
        for i, text in enumerate(context_texts)
    ])
    
    system_prompt = """Bạn là trợ lý tuyển sinh.

    QUY TẮC BẮT BUỘC:
    - Chỉ được trả lời dựa trên nội dung trong context. Không dùng kiến thức bên ngoài, không suy đoán thêm.
    - Không được mở đầu bằng các cụm như: "Dựa trên context", "Theo context", "Theo tài liệu được cung cấp", "Dựa trên thông tin được cung cấp".
    - Không nhắc tới từ "context" trong câu trả lời.
    - Nếu câu trả lời có trong context: trích dẫn hoặc tóm tắt từ context một cách chính xác, trả lời bằng tiếng Việt.
    - Nếu context không chứa thông tin để trả lời câu hỏi: hãy nói rõ "Theo các tài liệu được cung cấp, không có thông tin để trả lời câu hỏi này." và không bịa đáp án.
    - Trả lời trực tiếp, tự nhiên, rõ ràng bằng tiếng Việt."""

    user_prompt = f"""Thông tin tham khảo - - CHI dua vao day:

    {context_block}

    ---
    Câu hỏi: {prompt}

    Tra loi (chi dua tren context tren). 
    Hãy trả lời trực tiếp câu hỏi bằng tiếng Việt:"""

    # --------------------------------------------------
    # 3. Gọi LLM (Ollama proxy mặc định hoặc OpenAI)
    # --------------------------------------------------

    chat_url = f"{LLM_BASE_URL.rstrip('/')}/v1/chat/completions"
    llm_payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1000,
    }
    headers = {"Content-Type": "application/json"}
    if OPENAI_API_KEY:
        headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    t0 = time.time()
    try:
        llm_resp = requests.post(chat_url, json=llm_payload, headers=headers, timeout=60)
        llm_resp.raise_for_status()
        llm_data = llm_resp.json()
        answer = llm_data["choices"][0]["message"]["content"]
        model_used = llm_data.get("model", LLM_MODEL)
        usage = llm_data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
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
    if prompt_tokens is not None and completion_tokens is not None:
        tokens_used = prompt_tokens + completion_tokens

    # Format tuong thich Research Chat: status, content_markdown, meta
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
        # Giu them cho client LakeFlow neu can
        "answer": answer,
        "contexts": contexts,
    }