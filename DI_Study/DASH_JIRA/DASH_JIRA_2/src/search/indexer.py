import psycopg2
from psycopg2.extras import execute_values
from src.db.connection import get_db_connection
from src.nlp.llm_client import LLMClient
import time

def generate_embeddings_for_issues(batch_size=50, limit=None):
    conn = get_db_connection()
    cur = conn.cursor()
    llm = LLMClient()

    # Fetch issues that don't have embeddings yet
    # For simplicity, we'll just fetch all issues and check if they exist in embeddings table
    # In a real system, we'd have a more robust way to track indexed status
    
    query = """
        SELECT i.issue_key, i.summary, i.description 
        FROM issues i
        LEFT JOIN embeddings e ON i.issue_key = e.issue_key
        WHERE e.issue_key IS NULL
    """
    if limit:
        query += f" LIMIT {limit}"
        
    cur.execute(query)
    rows = cur.fetchall()
    print(f"Found {len(rows)} issues to index.")

    batch = []
    count = 0
    
    for row in rows:
        issue_key, summary, description = row
        text_to_embed = f"Summary: {summary}\nDescription: {description}"
        
        # Truncate if too long (simple check)
        if len(text_to_embed) > 8000:
            text_to_embed = text_to_embed[:8000]

        vector = llm.get_embedding(text_to_embed)
        
        if vector:
            batch.append((issue_key, 'full_context', vector, 'text-embedding-3-small'))
            count += 1
        
        if len(batch) >= batch_size:
            _insert_batch(conn, cur, batch)
            batch = []
            print(f"Indexed {count} issues...")
            time.sleep(0.5) # Rate limit protection

    if batch:
        _insert_batch(conn, cur, batch)
        
    print(f"Completed! Total indexed: {count}")
    cur.close()
    conn.close()

def _insert_batch(conn, cur, batch):
    insert_query = """
        INSERT INTO embeddings (issue_key, embedding_type, vector, model_version)
        VALUES %s
    """
    execute_values(cur, insert_query, batch)
    conn.commit()

if __name__ == "__main__":
    # Indexing a subset first to verify
    generate_embeddings_for_issues(batch_size=10, limit=50)
