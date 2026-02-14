from app.db.session import get_db_connection
from typing import List, Optional, Dict, Any
from datetime import datetime

class DoctorRepository:
    def __init__(self):
        pass

    def assign_patient(self, doctor_id: int, patient_id: int) -> bool:
        """
        Assign a patient to a doctor (grant read-only access).
        Returns True if successful, False if already assigned.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO doctor_patients (doctor_id, patient_id)
                VALUES (%s, %s)
                ON CONFLICT (doctor_id, patient_id) DO NOTHING
                RETURNING doctor_id
                """,
                (doctor_id, patient_id)
            )
            result = cursor.fetchone()
            conn.commit()
            return result is not None
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def revoke_access(self, doctor_id: int, patient_id: int) -> bool:
        """
        Revoke a doctor's access to a patient.
        Returns True if a row was deleted.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM doctor_patients WHERE doctor_id = %s AND patient_id = %s",
                (doctor_id, patient_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()
            conn.close()

    def get_patients_for_doctor(self, doctor_id: int) -> List[Dict[str, Any]]:
        """
        Get all patients assigned to a doctor.
        Returns list of patient info with tenant_id for data access.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT 
                    u.id, 
                    u.email, 
                    tu.tenant_id,
                    dp.granted_at
                FROM doctor_patients dp
                JOIN users u ON dp.patient_id = u.id
                LEFT JOIN tenant_users tu ON u.id = tu.user_id
                WHERE dp.doctor_id = %s
                ORDER BY dp.granted_at DESC
                """,
                (doctor_id,)
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "email": row[1],
                    "tenant_id": row[2],
                    "granted_at": row[3]
                }
                for row in rows
            ]
        finally:
            cursor.close()
            conn.close()

    def get_doctors_for_patient(self, patient_id: int) -> List[Dict[str, Any]]:
        """
        Get all doctors who have access to a patient's data.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT 
                    u.id, 
                    u.email,
                    dp.granted_at
                FROM doctor_patients dp
                JOIN users u ON dp.doctor_id = u.id
                WHERE dp.patient_id = %s
                ORDER BY dp.granted_at DESC
                """,
                (patient_id,)
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "email": row[1],
                    "granted_at": row[2]
                }
                for row in rows
            ]
        finally:
            cursor.close()
            conn.close()

    def is_doctor_assigned_to_patient(self, doctor_id: int, patient_id: int) -> bool:
        """
        Check if a doctor has access to a patient.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM doctor_patients WHERE doctor_id = %s AND patient_id = %s",
                (doctor_id, patient_id)
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()
            conn.close()
