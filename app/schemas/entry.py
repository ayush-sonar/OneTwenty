from pydantic import BaseModel, Field
from typing import Optional, Union, Any

class EntryBase(BaseModel):
    type: str = Field(default="sgv", description="Type of entry (sgv, mbg, etc)")
    dateString: str
    date: int
    sgv: Optional[int] = None
    direction: Optional[str] = None
    noise: Optional[int] = None
    filtered: Optional[int] = None
    unfiltered: Optional[int] = None
    rssi: Optional[int] = None
    device: Optional[str] = None
    
    # Allow extra fields for legacy compatibility
    class Config:
        extra = "allow"

class EntryCreate(EntryBase):
    pass

class EntryInDB(EntryBase):
    tenant_id: str
    _id: Any
