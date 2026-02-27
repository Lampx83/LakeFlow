from pydantic import BaseModel, Field
from typing import List, Optional


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=3)
    top_k: int = Field(default=5, ge=1, le=20)


class SemanticSearchResult(BaseModel):
    score: float
    file_hash: str
    chunk_id: str
    section_id: Optional[str]
    text: str
    token_estimate: Optional[int]


class SemanticSearchResponse(BaseModel):
    query: str
    results: List[SemanticSearchResult]
