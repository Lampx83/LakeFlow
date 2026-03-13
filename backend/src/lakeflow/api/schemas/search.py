from pydantic import BaseModel, Field
from typing import List, Optional


class EmbedRequest(BaseModel):
    """
    Request body for string vectorization (embedding) API.
    """
    text: str = Field(
        ...,
        min_length=1,
        description="String to vectorize (embed)",
    )


class EmbedResponse(BaseModel):
    """
    Response: vector embedding of string (dimension depends on model, default 384).
    """
    text: str = Field(..., description="String sent")
    vector: List[float] = Field(..., description="Vector embedding (normalized)")
    embedding: List[float] = Field(..., description="Alias of vector, for clients reading 'embedding'")
    dim: int = Field(..., description="Vector dimension")


class SemanticSearchRequest(BaseModel):
    """
    Request body for semantic search API.
    """
    query: str = Field(
        ...,
        min_length=1,
        description="Natural language query"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of results to return"
    )
    collection_name: Optional[str] = Field(
        None,
        description="Qdrant collection name (default: lakeflow_chunks)"
    )
    score_threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum score threshold (only return results with score >= threshold)"
    )
    qdrant_url: Optional[str] = Field(
        None,
        description="Qdrant Service URL (empty = default: localhost:6333 for dev, lakeflow-qdrant:6333 for docker)"
    )


class SemanticSearchResult(BaseModel):
    """
    A semantic search result.
    """
    id: Optional[str] = Field(
        None,
        description="Point ID in Qdrant"
    )
    score: float = Field(
        ...,
        description="Cosine similarity"
    )
    file_hash: Optional[str] = Field(
        None,
        description="Source file hash"
    )
    chunk_id: Optional[str] = Field(
        None,
        description="Chunk ID"
    )
    section_id: Optional[str] = Field(
        None,
        description="Section ID"
    )
    text: Optional[str] = Field(
        None,
        description="Chunk text content"
    )
    token_estimate: Optional[int] = Field(
        None,
        description="Token count estimate"
    )
    source: Optional[str] = Field(
        None,
        description="Point source (e.g. LakeFlow)"
    )


class SemanticSearchResponse(BaseModel):
    """
    Response for semantic search API.
    """
    query: str
    results: List[SemanticSearchResult]


class QARequest(BaseModel):
    """
    Request body for Q&A API.
    """
    question: str = Field(
        ...,
        min_length=1,
        description="User question"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of context chunks to use"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="LLM temperature"
    )
    collection_name: Optional[str] = Field(
        None,
        description="Qdrant collection name (default: lakeflow_chunks)"
    )
    score_threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum score when finding context"
    )
    qdrant_url: Optional[str] = Field(
        None,
        description="Qdrant Service URL (empty = default: localhost:6333 for dev, lakeflow-qdrant:6333 for docker)"
    )

class SourceItem(BaseModel):
    title: Optional[str] = None
    file: Optional[str] = None
    page: Optional[int] = None


class QADebugInfo(BaseModel):
    """Debug info: curl commands and step progress."""
    steps_completed: List[str] = Field(default_factory=list)
    curl_embed: Optional[str] = None
    curl_search: Optional[str] = None
    curl_complete: Optional[str] = None


class QAResponse(BaseModel):
    """
    Response for Q&A API.
    """
    question: str
    answer: str
    contexts: List[SemanticSearchResult] = Field(
        ...,
        description="Context chunks used"
    )
    sources: List[SourceItem] = Field(
        default_factory=list,
        description="Danh sách nguồn tài liệu để frontend hiển thị"
    )
    model_used: Optional[str] = Field(
        None,
        description="LLM model used"
    )
    debug_info: Optional[QADebugInfo] = Field(
        None,
        description="Curl commands to test each step + progress"
    )

# class QAResponse(BaseModel):
#     """
#     Response cho API Q&A
#     """
#     question: str
#     answer: str
#     contexts: List[SemanticSearchResult] = Field(
#         ...,
#         description="Các context chunks được sử dụng"
#     )
#     model_used: Optional[str] = Field(
#         None,
#         description="Model LLM được sử dụng"
#     )
