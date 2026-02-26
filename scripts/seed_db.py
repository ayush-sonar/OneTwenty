import sys
import os
import psycopg2
# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def init_db():
    conn = psycopg2.connect(settings.SQLALCHEMY_DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute("SELECT email FROM users WHERE email = %s", ('test@example.com',))
        if cursor.fetchone():
            print("DB already seeded")
            return

        # Insert Tenant
        print("Inserting Tenant...")
        cursor.execute(
            "INSERT INTO tenants (tenant_uuid, name, plan) VALUES (%s, %s, %s) RETURNING id",
            ("test-tenant-uuid", "Test Tenant", "pro")
        )
        tenant_id = cursor.fetchone()[0]
        
        # Insert User
        print("Inserting User...")
        cursor.execute(
            "INSERT INTO users (email, is_active, tenant_id, api_key) VALUES (%s, %s, %s, %s)",
            ("test@example.com", True, "test-tenant-uuid", "my-secret-api-key")
        )
        
        conn.commit()
        
        print("Seeding Complete!")
        print(f"User Email: test@example.com")
        print(f"API Key: my-secret-api-key")
        print(f"Tenant UUID: test-tenant-uuid")
        
    except Exception as e:
        conn.rollback()
        print(f"Error seeding DB: {e}")
    finally:
        cursor.close()
        conn.close()
    
if __name__ == "__main__":
    init_db()
