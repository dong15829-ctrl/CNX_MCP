import psycopg2
from src.config import settings

def count_embeddings():
    conn = psycopg2.connect(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname=settings.POSTGRES_DB,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM embeddings;")
    count = cur.fetchone()[0]
    print(f"Total embeddings in DB: {count}")
    conn.close()

if __name__ == "__main__":
    count_embeddings()
