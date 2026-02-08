from fastapi import APIRouter, HTTPException, Depends
import requests

from eduai.api.schemas.search import (
    EmbedRequest,
    EmbedResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    QARequest,
    QAResponse,
)
from eduai.api.deps import get_embedding_model
from eduai.core.auth import verify_token
from eduai.catalog.app_db import insert_message
from eduai.vectorstore.constants import COLLECTION_NAME as DEFAULT_COLLECTION_NAME
from eduai.core.config import get_qdrant_url, OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL

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
def qa(req: QARequest, payload: dict = Depends(verify_token)):
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
    # 3. Call OpenAI API (hoặc LLM khác)
    # --------------------------------------------------
    if not OPENAI_API_KEY:
        # Fallback: Trả về context nếu không có OpenAI key
        return {
            "question": req.question,
            "answer": "⚠️ Chưa cấu hình OpenAI API key. Vui lòng thêm OPENAI_API_KEY vào file .env để sử dụng tính năng Q&A.\n\nDưới đây là các context tìm được:\n\n" + "\n\n---\n\n".join(context_texts[:3]),
            "contexts": contexts,
            "model_used": None,
        }
    
    try:
        openai_url = f"{OPENAI_BASE_URL}/v1/chat/completions" if OPENAI_BASE_URL else "https://api.openai.com/v1/chat/completions"
        
        openai_payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": req.temperature,
            "max_tokens": 1000,
        }
        
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        
        openai_resp = requests.post(
            openai_url,
            json=openai_payload,
            headers=headers,
            timeout=30,
        )
        openai_resp.raise_for_status()
        
        openai_data = openai_resp.json()
        answer = openai_data["choices"][0]["message"]["content"]
        model_used = openai_data.get("model", OPENAI_MODEL)
        
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=500,
            detail=f"OpenAI API call failed: {exc}"
        )
    except (KeyError, IndexError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid OpenAI API response: {exc}"
        )

    # Ghi tin nhắn theo user (để thống kê / xóa trong Admin)
    try:
        insert_message(username=payload["sub"], question=req.question)
    except Exception:
        pass  # Không làm fail request Q&A nếu ghi DB lỗi

    return {
        "question": req.question,
        "answer": answer,
        "contexts": contexts,
        "model_used": model_used,
    }
