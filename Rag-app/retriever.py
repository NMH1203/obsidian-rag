import retriever as rt
from embedder import embed_query
 
def search(self, query, top_k=5, min_similarity=0.0):
        
    query_embedding = embed_query(query)
    cur = self.conn.cursor()
 
    cur.execute(
            """
            SELECT content, source, 1 - (embedding <=> %s::vector) AS similarity
            FROM notes
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, top_k)
        )
    
    results = cur.fetchall()
    cur.close()
 
        
    filtered = [r for r in results if r[2] >= min_similarity]
    return filtered


