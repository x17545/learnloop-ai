from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=1000,
    )


class SourceItem(BaseModel):
    page_number: int
    chunk_index: int
    text: str


class AskResponse(BaseModel):
    document_id: int
    question: str
    answer: str
    sources: list[SourceItem]