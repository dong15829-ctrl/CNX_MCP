import time
import psycopg2
from src.config import settings

def wait_for_db():
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                dbname=settings.POSTGRES_DB,
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT
            )
            print("Database connected successfully.")
            return conn
        except psycopg2.OperationalError:
            print("Waiting for database...")
            time.sleep(2)
            retries -= 1
    raise Exception("Could not connect to database.")

def verify_schema(conn):
    cur = conn.cursor()
    tables = ['issues', 'comments', 'embeddings']
    for table in tables:
        cur.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}');")
        exists = cur.fetchone()[0]
        if exists:
            print(f"Table '{table}' exists.")
        else:
            print(f"ERROR: Table '{table}' does not exist.")
    conn.close()

if __name__ == "__main__":
    conn = wait_for_db()
    verify_schema(conn)
