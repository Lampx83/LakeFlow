from fastapi import APIRouter, HTTPException, Depends
import requests

from lakeflow.api.schemas.search import (
    EmbedRequest,
    EmbedResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    QARequest,
    QAResponse,
)

from lakeflow.common.text_normalizer import canonicalize_text
from lakeflow.services.ollama_embed_service import embed_batch
from lakeflow.core.auth import verify_token
from lakeflow.catalog.app_db import insert_message
from lakeflow.vectorstore.constants import COLLECTION_NAME as DEFAULT_COLLECTION_NAME
from lakeflow.core.config import get_qdrant_url, LLM_BASE_URL, LLM_MODEL, OPENAI_API_KEY

import os
from lakeflow.catalog.db import get_connection
from lakeflow.config.paths import catalog_db_path

router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.post(
    "/embed",
    response_model=EmbedResponse,
    summary="Vector hóa chuỗi",
    description="Trả về vector embedding của một chuỗi (dùng cùng model với semantic search).",
)
def embed_text(req: EmbedRequest) -> dict:
    vector = embed_batch([req.text])[0]
    return {
        "text": req.text,
        "vector": vector,
        "embedding": vector,
        "dim": len(vector),
    }


@router.post(
    "/semantic",
    response_model=SemanticSearchResponse,
)
def semantic_search(req: SemanticSearchRequest):
    """
    Semantic search dùng Qdrant REST API (requests)
    """

    # --------------------------------------------------
    # 1. Embed query
    # --------------------------------------------------
    
    expanded_query = canonicalize_text(req.query)
    query_vector = embed_batch([expanded_query])[0]

    # --------------------------------------------------
    # 2. Call Qdrant REST API
    # --------------------------------------------------
    base = get_qdrant_url(req.qdrant_url)
    coll = (req.collection_name or DEFAULT_COLLECTION_NAME).strip() or DEFAULT_COLLECTION_NAME
    url = f"{base}/collections/{coll}/points/search"

    payload = {
        "vector": query_vector,
        "limit": req.top_k,
        "with_payload": True,
        "with_vector": False,
    }
    if req.score_threshold is not None:
        payload["score_threshold"] = req.score_threshold

    try:
        resp = requests.post(
            url,
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Qdrant search failed: {exc}")

    data = resp.json()

    # --------------------------------------------------
    # 3. Parse response
    # --------------------------------------------------
    points = data.get("result", [])

    results = []
    for p in points:
        pl = p.get("payload", {}) or {}
        results.append({
            "id": p.get("id"),
            "score": float(p.get("score", 0.0)),
            "file_hash": pl.get("file_hash"),
            "chunk_id": pl.get("chunk_id"),
            "section_id": pl.get("section_id"),
            "text": pl.get("text"),
            "token_estimate": pl.get("token_estimate"),
            "source": pl.get("source"),
        })

    return {
        "query": req.query,
        "results": results,
    }


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


@router.post(
    "/qa",
    response_model=QAResponse,
)
def qa(req: QARequest, auth_payload: dict = Depends(verify_token)):
    """
    Q&A với RAG: Tìm context từ semantic search, sau đó dùng LLM để trả lời.
    Tin nhắn (câu hỏi) được ghi theo username để thống kê trong Admin.
    """
    # --------------------------------------------------
    # 1. Semantic search để lấy context
    # --------------------------------------------------
    expanded_query = canonicalize_text(req.question)    
    query_vector = embed_batch([expanded_query])[0]
    
    base = get_qdrant_url(req.qdrant_url)
    coll = (req.collection_name or DEFAULT_COLLECTION_NAME).strip() or DEFAULT_COLLECTION_NAME
    url = f"{base}/collections/{coll}/points/search"

    search_body = {
        "vector": query_vector,
        "limit": req.top_k,
        "with_payload": True,
        "with_vector": False,
    }
    if req.score_threshold is not None:
        search_body["score_threshold"] = req.score_threshold

    try:
        resp = requests.post(
            url,
            json=search_body,
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Qdrant search failed: {exc}"
        )

    data = resp.json()
    points = data.get("result", [])

    if not points:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy context phù hợp để trả lời câu hỏi"
        )

    # Parse context results
    contexts = []
    context_texts = []

    for p in points:
        pl = p.get("payload", {}) or {}
        context_text = pl.get("text", "")
        contexts.append({
            "id": p.get("id"),
            "score": float(p.get("score", 0.0)),
            "file_hash": pl.get("file_hash"),
            "chunk_id": pl.get("chunk_id"),
            "section_id": pl.get("section_id"),
            "text": context_text,
            "token_estimate": pl.get("token_estimate"),
            "source": pl.get("source"),
        })
        
        if context_text:
            context_texts.append(context_text)
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

    user_prompt = f"""Thông tin tham khảo:

    {context_block}

    ---
    Câu hỏi: {req.question}

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
        "temperature": req.temperature,
        "max_tokens": 1000,
    }
    headers = {"Content-Type": "application/json"}
    if OPENAI_API_KEY:
        headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    try:
        llm_resp = requests.post(
            chat_url,
            json=llm_payload,
            headers=headers,
            timeout=60,
        )
        llm_resp.raise_for_status()
        llm_data = llm_resp.json()
        answer = llm_data["choices"][0]["message"]["content"]
        model_used = llm_data.get("model", LLM_MODEL)
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=500,
            detail=f"LLM API call failed: {exc}",
        )
    except (KeyError, IndexError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid LLM API response: {exc}",
        )

    # Ghi tin nhắn theo user (để thống kê / xóa trong Admin)
    try:
        insert_message(username=auth_payload["sub"], question=req.question)
    except Exception:
        pass  # Không làm fail request Q&A nếu ghi DB lỗi
    
    return {
        "question": req.question,
        "answer": answer,
        "contexts": contexts,
        "sources": sources,
        "model_used": model_used,
        
    }
