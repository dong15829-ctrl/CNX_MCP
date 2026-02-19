import psycopg2
from src.config import settings

def check_schema():
    conn = psycopg2.connect(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname=settings.POSTGRES_DB,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT character_maximum_length 
        FROM information_schema.columns 
        WHERE table_name = 'issues' AND column_name = 'issue_key';
    """)
    length = cur.fetchone()[0]
    print(f"Current issue_key length: {length}")
    conn.close()

if __name__ == "__main__":
    check_schema()
