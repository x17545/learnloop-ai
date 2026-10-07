from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    stored_filename: str
    content_type: str
    status: str
    uploaded_at: datetime

    model_config = {
        "from_attributes": True
    }