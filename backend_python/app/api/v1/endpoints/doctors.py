from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_tenant_from_jwt, get_current_user_id
from app.repositories.doctor import DoctorRepository
from app.repositories.user import UserRepository
from app.schemas.rbac import DoctorInfo, PatientInfo
from app.core.logging import logger
from typing import List

router = APIRouter()

@router.post("/assign-patient")
async def assign_patient(
    patient_email: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Assign a patient to the logged-in doctor.
    Only users with 'doctor' role can call this.
    Patients must grant access by providing their email.
    """
    user_repo = UserRepository()
    doctor_repo = DoctorRepository()
    
    # Get current user info
    current_user = user_repo.get_by_email(
        user_repo.get_email_by_id(user_id)
    )
    
    if not current_user or current_user.get("role") != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can assign patients")
    
    # Find patient by email
    patient = user_repo.get_by_email(patient_email)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    if patient.get("role") != "user":
        raise HTTPException(status_code=400, detail="Can only assign regular users as patients")
    
    # Assign
    success = doctor_repo.assign_patient(user_id, patient["id"])
    
    logger.info(
        "Doctor assigned to patient",
        extra={
            'extra_data': {
                'doctor_id': user_id,
                'patient_id': patient["id"],
                'patient_email': patient_email
            }
        }
    )
    
    return {
        "status": "ok",
        "message": "Patient assigned successfully" if success else "Patient already assigned"
    }

@router.get("/my-patients", response_model=List[PatientInfo])
async def get_my_patients(user_id: int = Depends(get_current_user_id)):
    """
    Get all patients assigned to the logged-in doctor.
    """
    user_repo = UserRepository()
    doctor_repo = DoctorRepository()
    
    # Verify user is a doctor
    current_user = user_repo.get_by_email(
        user_repo.get_email_by_id(user_id)
    )
    
    if not current_user or current_user.get("role") != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can view patients")
    
    patients = doctor_repo.get_patients_for_doctor(user_id)
    return patients

@router.get("/my-doctors", response_model=List[DoctorInfo])
async def get_my_doctors(user_id: int = Depends(get_current_user_id)):
    """
    Get all doctors who have access to the logged-in user's data.
    """
    doctor_repo = DoctorRepository()
    doctors = doctor_repo.get_doctors_for_patient(user_id)
    return doctors

@router.delete("/revoke/{doctor_id}")
async def revoke_doctor_access(
    doctor_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    Revoke a doctor's access to the logged-in user's data.
    """
    doctor_repo = DoctorRepository()
    
    success = doctor_repo.revoke_access(doctor_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Doctor access not found")
    
    logger.info(
        "Doctor access revoked",
        extra={
            'extra_data': {
                'doctor_id': doctor_id,
                'patient_id': user_id
            }
        }
    )
    
    return {
        "status": "ok",
        "message": "Doctor access revoked successfully"
    }
