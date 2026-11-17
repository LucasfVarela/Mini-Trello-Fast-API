from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    original_name: str
    content_type: str
    size: int
    uploaded_by_id: int
    uploaded_at: datetime
