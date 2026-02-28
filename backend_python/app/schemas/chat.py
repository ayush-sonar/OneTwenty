from pydantic import BaseModel, Field
from typing import Optional

class ChatBase(BaseModel):
    userMessage: str
    aiResponse: str
    tenant_id: str

class ChatCreate(ChatBase):
    date: Optional[int] = None
    dateString: Optional[str] = None

class ChatInDB(ChatBase):
    id: str = Field(alias="_id")
    date: int
    dateString: str

    class Config:
        populate_by_name = True
