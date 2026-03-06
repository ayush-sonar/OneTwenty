import psycopg2
from app.core.config import settings

def get_db_connection():
    """
    Returns a raw psycopg2 connection.
    Users of this function are responsible for closing the connection.
    """
    conn = psycopg2.connect(settings.SQLALCHEMY_DATABASE_URL)
    return conn
