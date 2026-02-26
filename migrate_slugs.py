import os
import sys
import string
import random
import psycopg2
from urllib.parse import urlparse

# Add parent directory to path to import app modules if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database URL from environment or hardcoded for local testing
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable not set.")
        sys.exit(1)
    return psycopg2.connect(DATABASE_URL)

def generate_slug(length=9):
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def migrate_slugs():
    print("Starting slug migration...")
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Get all tenants
        cursor.execute("SELECT id, name, slug FROM tenants")
        tenants = cursor.fetchall()
        print(f"Found {len(tenants)} tenants.")

        updated_count = 0
        
        for tenant in tenants:
            tenant_id, name, current_slug = tenant
            
            # Check if slug is valid (9 chars, alphanumeric)
            is_valid = False
            if current_slug and len(current_slug) == 9:
                is_valid = all(c in string.ascii_lowercase + string.digits for c in current_slug)
            
            if not is_valid:
                new_slug = generate_slug()
                print(f"Updating Tenant {tenant_id} ({name}): '{current_slug}' -> '{new_slug}'")
                
                cursor.execute(
                    "UPDATE tenants SET slug = %s WHERE id = %s",
                    (new_slug, tenant_id)
                )
                updated_count += 1
            else:
                print(f"Tenant {tenant_id} ({name}) already has valid slug: '{current_slug}'")

        conn.commit()
        print(f"Migration complete. Updated {updated_count} tenants.")

    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    if not DATABASE_URL:
        # Try to load from secrets.json for local dev
        try:
            import json
            with open('../backend_python/secrets.json') as f:
                secrets = json.load(f)
                DATABASE_URL = secrets.get("SQLALCHEMY_DATABASE_URL")
        except:
            pass
            
    migrate_slugs()
