from embedder import embed_query
from database import get_connection

def search_top_k(query: str, top_k: int = 5, min_similarity: float = 0.0, conn=None) -> list:
    if not query or not query.strip():
        return []

    # Create vector embedding for query
    query_embedding = embed_query(query)
    if not query_embedding:
        print("Could not embed query.")
        return []

    should_close_conn = False
    if conn is None:
        conn = get_connection()
        should_close_conn = True

    if not conn:
        print("Could not connect to database.")
        return []

    try:
        cur = conn.cursor()
        
        # Use <=>< in pgvector to calculate Cosine Distance
        # Cosine Similarity = 1 - Cosine Distance
        query_sql = """
            SELECT id, content, source, content_hash, 1 - (embedding <=> %s::vector) AS similarity
            FROM notes
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        
        query_embedding_str = str(query_embedding)
        cur.execute(query_sql, (query_embedding_str, query_embedding_str, top_k))
        rows = cur.fetchall()
        cur.close()

        results = []
        for r in rows:
            similarity = float(r[4]) if r[4] is not None else 0.0
            if similarity >= min_similarity:
                results.append({
                    "id": r[0],
                    "content": r[1],
                    "source": r[2],
                    "content_hash": r[3],
                    "similarity": round(similarity, 4)
                })

        return results
    except Exception as e:
        print(f"Error when perform search top k: {e}")
        return []
    finally:
        if should_close_conn and conn:
            conn.close()

#Class retriever to manage connections and perform Top-K queries.
class Retriever:
    def __init__(self, conn=None):
        self.conn = conn

    def search(self, query: str, top_k: int = 5, min_similarity: float = 0.0) -> list:
        return search_top_k(query, top_k=top_k, min_similarity=min_similarity, conn=self.conn)
