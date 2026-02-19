import psycopg2
from typing import List, Dict, Any
from src.db.connection import get_db_connection
from src.nlp.llm_client import LLMClient

class VectorStore:
    def __init__(self):
        self.llm_client = LLMClient() # Used for embedding generation if needed locally
        # Note: In a real scenario, we might use a separate embedding service.
        # Here we assume we can get embeddings via OpenAI client (not implemented in LLMClient yet, but placeholder)

    def search_similar_cases(self, query_text: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Searches for similar cases using vector similarity.
        """
        # 1. Generate embedding for the query
        query_vector = self.llm_client.get_embedding(query_text)
        
        if not query_vector:
            return []
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            # Use pgvector's cosine distance operator (<=>)
            # 1 - distance = similarity
            cur.execute("""
                SELECT i.issue_key, i.summary, i.description, i.status, 1 - (e.vector <=> %s::vector) as similarity
                FROM issues i
                JOIN embeddings e ON i.issue_key = e.issue_key
                ORDER BY similarity DESC
                LIMIT %s
            """, (query_vector, limit))
            
            results = []
            for row in cur.fetchall():
                results.append({
                    "issue_key": row[0],
                    "summary": row[1],
                    "description": row[2] or "", # Handle None
                    "status": row[3],
                    "similarity": float(row[4])
                })
            
            return results
            
        except Exception as e:
            print(f"Vector search failed: {e}")
            return []
        finally:
            cur.close()
            conn.close()
