import sys
import os
import psycopg2
# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def init_db_schema():
    print(f"Connecting to: {settings.SQLALCHEMY_DATABASE_URL.split('@')[1]}") # Hide credentials
    conn = psycopg2.connect(settings.SQLALCHEMY_DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    ddl_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "DDLs", "02_auth.sql")
    
    with open(ddl_path, "r") as f:
        sql = f.read()
        
    try:
        print("Executing DDLs from 02_auth.sql...")
        cursor.execute(sql)
        print("Schema initialized successfully!")
    except Exception as e:
        print(f"Error executing DDL: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    init_db_schema()
