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
from lakeflow.api.deps import get_embedding_model
from lakeflow.core.auth import verify_token
from lakeflow.catalog.app_db import insert_message
from lakeflow.vectorstore.constants import COLLECTION_NAME as DEFAULT_COLLECTION_NAME
from lakeflow.core.config import get_qdrant_url, LLM_BASE_URL, LLM_MODEL, OPENAI_API_KEY

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
    """
    Vector hóa (embed) một chuỗi. Dùng model sentence-transformers (mặc định all-MiniLM-L6-v2).
    Vector được chuẩn hóa (normalize), phù hợp so sánh cosine similarity.
    """
    model = get_embedding_model()
    vector = model.encode(
        req.text,
        normalize_embeddings=True,
    ).astype("float32")
    vec_list = vector.tolist()
    return {
        "text": req.text,
        "vector": vec_list,
        "embedding": vec_list,  # alias cho client chỉ đọc "embedding" (vd. Research Chat)
        "dim": int(vector.shape[0]),
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
    model = get_embedding_model()

    query_vector = model.encode(
        req.query,
        normalize_embeddings=True,
    ).tolist()

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
    model = get_embedding_model()
    
    query_vector = model.encode(
        req.question,
        normalize_embeddings=True,
    ).tolist()
    
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
    
    # --------------------------------------------------
    # 2. Build prompt với context
    # --------------------------------------------------
    context_block = "\n\n".join([
        f"[Context {i+1}]:\n{text}"
        for i, text in enumerate(context_texts)
    ])
    
    system_prompt = """Bạn đang tham gia một demo RAG (Retrieval-Augmented Generation). Nhiệm vụ của bạn là trả lời câu hỏi CHỈ dựa trên các đoạn tài liệu (context) được cung cấp bên dưới.

QUY TẮC BẮT BUỘC:
- Chỉ được trả lời dựa trên nội dung trong context. Không dùng kiến thức bên ngoài, không suy đoán thêm.
- Nếu câu trả lời có trong context: trích dẫn hoặc tóm tắt từ context một cách chính xác, trả lời bằng tiếng Việt.
- Nếu context không chứa thông tin để trả lời câu hỏi: hãy nói rõ "Theo các tài liệu được cung cấp, không có thông tin để trả lời câu hỏi này." và không bịa đáp án.
- Trả lời ngắn gọn, rõ ràng, bằng tiếng Việt."""

    user_prompt = f"""Các đoạn tài liệu (context) dùng để trả lời — CHỈ dựa vào đây:

{context_block}

---
Câu hỏi: {req.question}

Trả lời (chỉ dựa trên context trên):"""
    
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
        "model_used": model_used,
    }
