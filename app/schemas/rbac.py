from enum import Enum
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserRole(str, Enum):
    """User roles in the system"""
    ADMIN = "admin"
    DOCTOR = "doctor"
    USER = "user"

class UserTier(str, Enum):
    """Subscription tiers"""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class DoctorPatientAssignment(BaseModel):
    """Schema for doctor-patient relationship"""
    doctor_id: int
    patient_id: int
    granted_at: Optional[datetime] = None

class DoctorInfo(BaseModel):
    """Doctor information for patient view"""
    id: int
    email: str
    granted_at: datetime

class PatientInfo(BaseModel):
    """Patient information for doctor view"""
    id: int
    email: str
    tenant_id: int
    granted_at: datetime
