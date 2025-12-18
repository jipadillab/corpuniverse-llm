from typing import List
import numpy as np

def retrieve_context(query: str, index, chunks: List[str], embedder, top_k: int = 5) -> List[str]:
    q = embedder.encode([query], normalize_embeddings=True).astype("float32")
    scores, ids = index.search(q, top_k)
    results = []
    for i in ids[0]:
        if 0 <= i < len(chunks):
            results.append(chunks[i])
    return results
