from app.db.session import get_db_connection
from typing import Optional, List, Dict, Any
from datetime import datetime

class ClockRepository:
    def get_by_clock_id(self, clock_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, clock_id, wifi_name, wifi_password, user_subdomain_url, created_at, updated_at FROM clock_configs WHERE clock_id = %s",
                (clock_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "clock_id": row[1],
                    "wifi_name": row[2],
                    "wifi_password": row[3],
                    "user_subdomain_url": row[4],
                    "created_at": row[5],
                    "updated_at": row[6]
                }
            return None
        finally:
            cursor.close()
            conn.close()

    def create(self, clock_id: str, wifi_name: Optional[str], wifi_password: Optional[str], user_subdomain_url: Optional[str]) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO clock_configs (clock_id, wifi_name, wifi_password, user_subdomain_url) 
                   VALUES (%s, %s, %s, %s) 
                   RETURNING id, clock_id, wifi_name, wifi_password, user_subdomain_url, created_at, updated_at""",
                (clock_id, wifi_name, wifi_password, user_subdomain_url)
            )
            row = cursor.fetchone()
            conn.commit()
            return {
                "id": row[0],
                "clock_id": row[1],
                "wifi_name": row[2],
                "wifi_password": row[3],
                "user_subdomain_url": row[4],
                "created_at": row[5],
                "updated_at": row[6]
            }
        finally:
            cursor.close()
            conn.close()

    def update(self, clock_id: str, wifi_name: Optional[str] = None, wifi_password: Optional[str] = None, user_subdomain_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            updates = []
            params = []
            
            if wifi_name is not None:
                updates.append("wifi_name = %s")
                params.append(wifi_name)
            if wifi_password is not None:
                updates.append("wifi_password = %s")
                params.append(wifi_password)
            if user_subdomain_url is not None:
                updates.append("user_subdomain_url = %s")
                params.append(user_subdomain_url)
            
            if not updates:
                return self.get_by_clock_id(clock_id)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            
            query = f"UPDATE clock_configs SET {', '.join(updates)} WHERE clock_id = %s RETURNING id, clock_id, wifi_name, wifi_password, user_subdomain_url, created_at, updated_at"
            params.append(clock_id)
            
            cursor.execute(query, tuple(params))
            row = cursor.fetchone()
            conn.commit()
            if row:
                return {
                    "id": row[0],
                    "clock_id": row[1],
                    "wifi_name": row[2],
                    "wifi_password": row[3],
                    "user_subdomain_url": row[4],
                    "created_at": row[5],
                    "updated_at": row[6]
                }
            return None
        finally:
            cursor.close()
            conn.close()

    def assign_to_subdomain(self, clock_id: str, user_subdomain_url: str) -> Optional[Dict[str, Any]]:
        return self.update(clock_id=clock_id, user_subdomain_url=user_subdomain_url)
