import psycopg2
from psycopg2.extras import RealDictCursor
from src.config import settings

def get_db_connection():
    conn = psycopg2.connect(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname=settings.POSTGRES_DB,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT
    )
    return conn
