"""
Load NIST 800-171 knowledge base into Qdrant for RAG retrieval.

1. Chunks controls, objectives, and family overviews
2. Generates embeddings using BGE-small (CPU)
3. Creates/recreates Qdrant collection with proper config
4. Upserts all vectors with metadata for filtered search

Usage:
  cd D:\cmmc-platform
  python scripts\load_nist_to_qdrant.py

Requires: Qdrant running on localhost:6333
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    PayloadSchemaType,
    TextIndexParams,
    TokenizerType,
)

from configs.settings import QDRANT_HOST, QDRANT_PORT
from src.rag.chunker import get_all_chunks
from src.rag.embedder import get_embedding_service

# Collection name for NIST compliance knowledge
COLLECTION_NAME = "nist_compliance"


def create_collection(client: QdrantClient, dimension: int):
    """Create or recreate the Qdrant collection with optimized settings."""
    print(f"\nCreating collection '{COLLECTION_NAME}' (dim={dimension})...")

    # Delete if exists (clean reload)
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME in collections:
        print(f"  Deleting existing collection...")
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=dimension,
            distance=Distance.COSINE,
            on_disk=False,  # Keep in RAM for dev (small dataset)
        ),
    )

    # Create payload indexes for filtered search
    print("  Creating payload indexes...")

    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="type",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="control_id",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="family_id",
        field_schema=PayloadSchemaType.KEYWORD,
    )

    # Full-text index on the text field for hybrid search
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="text",
        field_schema=TextIndexParams(
            type="text",
            tokenizer=TokenizerType.WORD,
            min_token_len=2,
            max_token_len=20,
            lowercase=True,
        ),
    )

    print(f"  Collection '{COLLECTION_NAME}' created successfully")


def embed_and_upload(client: QdrantClient, chunks, embedding_service):
    """Embed all chunks and upload to Qdrant in batches."""
    print(f"\nEmbedding {len(chunks)} chunks...")

    # Extract texts for embedding
    texts = [chunk["text"] for chunk in chunks]

    # Embed in batches (BGE-small is fast on CPU)
    start = time.time()
    embeddings = embedding_service.embed_documents(texts)
    elapsed = time.time() - start
    print(f"  Embedded {len(texts)} chunks in {elapsed:.1f}s "
          f"({len(texts)/elapsed:.0f} chunks/sec)")

    # Build Qdrant points
    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        payload = {
            "text": chunk["text"],
            **chunk["metadata"],
        }
        points.append(PointStruct(
            id=i,
            vector=embedding,
            payload=payload,
        ))

    # Upload in batches of 100
    BATCH_SIZE = 100
    print(f"\nUploading {len(points)} points to Qdrant...")
    for batch_start in range(0, len(points), BATCH_SIZE):
        batch = points[batch_start:batch_start + BATCH_SIZE]
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=batch,
        )
        print(f"  Uploaded batch {batch_start // BATCH_SIZE + 1} "
              f"({batch_start + len(batch)}/{len(points)})")

    # Verify
    info = client.get_collection(COLLECTION_NAME)
    print(f"\nCollection stats:")
    print(f"  Points: {info.points_count}")
    print(f"  Status: {info.status}")


def test_search(client: QdrantClient, embedding_service):
    """Run sample queries to verify RAG works."""
    print("\n" + "=" * 60)
    print("RAG VERIFICATION — Sample Queries")
    print("=" * 60)

    test_queries = [
        "What does AC.L2-3.1.1 require?",
        "multifactor authentication requirements",
        "CUI encryption FIPS validated",
        "What evidence do I need for access control?",
        "POA&M eligibility rules",
        "incident response capability testing",
    ]

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        q_embedding = embedding_service.embed_query(query)

        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=q_embedding,
            limit=3,
            with_payload=True,
        ).points

        for j, hit in enumerate(results):
            score = hit.score
            payload = hit.payload
            chunk_type = payload.get("type", "?")
            ctrl_id = payload.get("control_id", "—")
            text_preview = payload.get("text", "")[:120].replace("\n", " ")
            print(f"  [{j+1}] score={score:.4f} | type={chunk_type} | "
                  f"control={ctrl_id}")
            print(f"      {text_preview}...")

    print("\n" + "=" * 60)
    print("RAG verification complete!")
    print("=" * 60)


def main():
    print("=" * 60)
    print("NIST 800-171 — Load Knowledge Base to Qdrant")
    print("=" * 60)

    # Connect to Qdrant
    print(f"\nConnecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # Initialize embedding service
    embedding_service = get_embedding_service()

    # Create collection
    create_collection(client, embedding_service.dimension)

    # Generate chunks
    chunks = get_all_chunks()

    # Embed and upload
    embed_and_upload(client, chunks, embedding_service)

    # Test search
    test_search(client, embedding_service)

    print("\nDone! Qdrant collection ready for RAG queries.")


if __name__ == "__main__":
    main()