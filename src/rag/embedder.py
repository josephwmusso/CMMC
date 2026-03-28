"""
Embedding service for the CMMC compliance platform.

Dev:  BAAI/bge-small-en-v1.5 (33M params, 384-dim, runs on CPU)
Prod: Snowflake/snowflake-arctic-embed-l-v2.0 (Apache 2.0, US-origin, GPU)

BGE models expect a query prefix for retrieval tasks.
"""

import os
import time
from typing import List

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None  # Not installed on Render free tier

# Model selection
MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "BAAI/bge-small-en-v1.5"  # 130MB, CPU-friendly, 384-dim
)

# BGE models use this prefix for queries (not for documents)
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class EmbeddingService:
    """Wraps sentence-transformers for embedding generation."""

    def __init__(self, model_name: str = MODEL_NAME):
        print(f"Loading embedding model: {model_name}")
        start = time.time()
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        elapsed = time.time() - start
        print(f"Model loaded in {elapsed:.1f}s — dimension: {self.dimension}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed document chunks (no prefix for BGE)."""
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 50,
            batch_size=32
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """Embed a search query (with BGE prefix)."""
        prefixed = BGE_QUERY_PREFIX + query
        embedding = self.model.encode(
            [prefixed],
            normalize_embeddings=True
        )
        return embedding[0].tolist()


# Singleton for reuse across the app
_service = None


def get_embedding_service() -> EmbeddingService:
    global _service
    if _service is None:
        _service = EmbeddingService()
    return _service


if __name__ == "__main__":
    # Quick test
    svc = get_embedding_service()
    doc_emb = svc.embed_documents(["NIST 800-171 access control requirement"])
    q_emb = svc.embed_query("What does AC.L2-3.1.1 require?")
    print(f"Document embedding dim: {len(doc_emb[0])}")
    print(f"Query embedding dim: {len(q_emb)}")
    print(f"First 5 values (doc): {doc_emb[0][:5]}")
    print(f"First 5 values (query): {q_emb[:5]}")

    # Similarity check
    import numpy as np
    sim = np.dot(doc_emb[0], q_emb)
    print(f"Cosine similarity: {sim:.4f}")

_model = None

def get_embedder():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('BAAI/bge-small-en-v1.5')
    return _model
