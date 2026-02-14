from app.db.session import get_db_connection

def get_email_by_id(user_id: int) -> str:
    """Helper function to get email by user ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        cursor.close()
        conn.close()
