import json
from app.db.session import get_db_connection
from typing import Optional, Dict, Any

class TenantRepository:
    def __init__(self):
        pass

    def get_settings(self, tenant_id: int) -> Dict[str, Any]:
        """
        Fetch the settings JSONB for a tenant.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT settings FROM tenants WHERE id = %s",
                (tenant_id,)
            )
            row = cursor.fetchone()
            if row and row[0]:
                return row[0]  # psycopg2 automatically deserializes JSONB to dict
            return {}
        finally:
            cursor.close()
            conn.close()

    def update_settings(self, tenant_id: int, settings: Dict[str, Any]):
        """
        Update the settings JSONB for a tenant.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE tenants SET settings = %s WHERE id = %s",
                (json.dumps(settings), tenant_id)
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def get_tenant_info(self, tenant_id: int) -> Optional[Dict[str, Any]]:
        """
        Get basic tenant info (name, slug, etc.)
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, public_id, name, slug, plan, settings FROM tenants WHERE id = %s",
                (tenant_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "public_id": row[1],
                    "name": row[2],
                    "slug": row[3],
                    "plan": row[4],
                    "settings": row[5]
                }
            return None
        finally:
            cursor.close()
            conn.close()
