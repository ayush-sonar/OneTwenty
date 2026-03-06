from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ClockConfigBase(BaseModel):
    clock_id: str = Field(..., description="Alphanumeric unique identifier for the clock")
    wifi_name: Optional[str] = None
    wifi_password: Optional[str] = None
    user_subdomain_url: Optional[str] = None

class ClockConfigCreate(ClockConfigBase):
    pass

class ClockConfigUpdate(BaseModel):
    wifi_name: Optional[str] = None
    wifi_password: Optional[str] = None
    user_subdomain_url: Optional[str] = None

class ClockConfigResponse(ClockConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ClockAssignment(BaseModel):
    clock_id: str
    user_subdomain_url: str
