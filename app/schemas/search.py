from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=500,
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=10,
    )


class SearchResult(BaseModel):
    text: str
    page_number: int
    chunk_index: int
    distance: float | None = None


class SearchResponse(BaseModel):
    document_id: int
    query: str
    results: list[SearchResult]