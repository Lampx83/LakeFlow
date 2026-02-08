from pydantic import BaseModel, Field
from typing import List, Optional


class EmbedRequest(BaseModel):
    """
    Request body cho API vector hóa chuỗi (embedding)
    """
    text: str = Field(
        ...,
        min_length=1,
        description="Chuỗi cần vector hóa (embed)",
    )


class EmbedResponse(BaseModel):
    """
    Response: vector embedding của chuỗi (chiều phụ thuộc model, mặc định 384)
    """
    text: str = Field(..., description="Chuỗi đã gửi")
    vector: List[float] = Field(..., description="Vector embedding (normalized)")
    embedding: List[float] = Field(..., description="Alias của vector, cho client chỉ đọc 'embedding'")
    dim: int = Field(..., description="Số chiều của vector")


class SemanticSearchRequest(BaseModel):
    """
    Request body cho API semantic search
    """
    query: str = Field(
        ...,
        min_length=1,
        description="Câu truy vấn ngôn ngữ tự nhiên"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Số lượng kết quả trả về"
    )
    collection_name: Optional[str] = Field(
        None,
        description="Tên collection Qdrant (mặc định: eduai_chunks)"
    )
    score_threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Ngưỡng điểm tối thiểu (chỉ trả về kết quả có score >= ngưỡng)"
    )
    qdrant_url: Optional[str] = Field(
        None,
        description="URL Qdrant Service (trống = mặc định: localhost:6333 khi dev, eduai-qdrant:6333 khi docker)"
    )


class SemanticSearchResult(BaseModel):
    """
    Một kết quả semantic search
    """
    id: Optional[str] = Field(
        None,
        description="Định danh point trong Qdrant"
    )
    score: float = Field(
        ...,
        description="Độ tương đồng cosine"
    )
    file_hash: Optional[str] = Field(
        None,
        description="Hash của file nguồn"
    )
    chunk_id: Optional[str] = Field(
        None,
        description="ID của chunk"
    )
    section_id: Optional[str] = Field(
        None,
        description="ID của section"
    )
    text: Optional[str] = Field(
        None,
        description="Nội dung text của chunk"
    )
    token_estimate: Optional[int] = Field(
        None,
        description="Ước lượng số token"
    )
    source: Optional[str] = Field(
        None,
        description="Nguồn point (ví dụ EDUAI)"
    )


class SemanticSearchResponse(BaseModel):
    """
    Response cho API semantic search
    """
    query: str
    results: List[SemanticSearchResult]


class QARequest(BaseModel):
    """
    Request body cho API Q&A
    """
    question: str = Field(
        ...,
        min_length=1,
        description="Câu hỏi của người dùng"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Số lượng context chunks để sử dụng"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature cho LLM"
    )
    collection_name: Optional[str] = Field(
        None,
        description="Tên collection Qdrant (mặc định: eduai_chunks)"
    )
    score_threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Ngưỡng điểm tối thiểu khi tìm context"
    )
    qdrant_url: Optional[str] = Field(
        None,
        description="URL Qdrant Service (trống = mặc định: localhost:6333 khi dev, eduai-qdrant:6333 khi docker)"
    )


class QAResponse(BaseModel):
    """
    Response cho API Q&A
    """
    question: str
    answer: str
    contexts: List[SemanticSearchResult] = Field(
        ...,
        description="Các context chunks được sử dụng"
    )
    model_used: Optional[str] = Field(
        None,
        description="Model LLM được sử dụng"
    )
