"""
Week 2, Step 2 — End-to-End Verification

Checks:
1. Postgres has all 110 controls and 246 objectives
2. Qdrant collection exists with all chunks
3. RAG query returns relevant results for control-specific questions
4. Metadata filtering works (search by family, type)
5. SPRS scoring integrity check

Usage:
  cd D:\cmmc-platform
  python scripts\verify_rag.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from configs.settings import DATABASE_URL, QDRANT_HOST, QDRANT_PORT
from src.rag.embedder import get_embedding_service

COLLECTION_NAME = "nist_compliance"
PASS = "PASS"
FAIL = "FAIL"


def check(name, condition, detail=""):
    status = PASS if condition else FAIL
    msg = f"[{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return condition


def verify_postgres():
    """Check Postgres data integrity."""
    print("\n" + "=" * 60)
    print("1. POSTGRES VERIFICATION")
    print("=" * 60)

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # Control count
        count = conn.execute(text("SELECT COUNT(*) FROM controls")).scalar()
        check("Control count", count == 110, f"expected 110, got {count}")

        # Objective count
        obj_count = conn.execute(
            text("SELECT COUNT(*) FROM assessment_objectives")
        ).scalar()
        check("Objective count", obj_count >= 240,
              f"expected 240+, got {obj_count}")

        # All 14 families present
        families = conn.execute(
            text("SELECT DISTINCT family FROM controls")
        ).fetchall()
        check("Family count", len(families) == 14,
              f"expected 14, got {len(families)}")

        # SPRS integrity
        five_pt = conn.execute(
            text("SELECT COUNT(*) FROM controls WHERE points = 5")
        ).scalar()
        three_pt = conn.execute(
            text("SELECT COUNT(*) FROM controls WHERE points = 3")
        ).scalar()
        one_pt = conn.execute(
            text("SELECT COUNT(*) FROM controls WHERE points = 1")
        ).scalar()
        check("SPRS 5-point controls", five_pt == 11, f"got {five_pt}")
        check("SPRS 3-point controls", three_pt == 22, f"got {three_pt}")
        check("SPRS 1-point controls", one_pt == 77, f"got {one_pt}")
        check("Total controls sum", five_pt + three_pt + one_pt == 110)

        # SSP cannot be POA&M'd
        ssp = conn.execute(text(
            "SELECT poam_eligible FROM controls WHERE id = 'CA.L2-3.12.4'"
        )).scalar()
        check("SSP not POA&M eligible", ssp in ("no", False),
              f"CA.L2-3.12.4 poam_eligible = '{ssp}'")

        # Every objective links to a valid control
        orphans = conn.execute(text("""
            SELECT ao.id FROM assessment_objectives ao
            LEFT JOIN controls c ON ao.control_id = c.id
            WHERE c.id IS NULL
        """)).fetchall()
        check("No orphan objectives", len(orphans) == 0,
              f"{len(orphans)} orphans found")

        # All controls have at least 1 objective
        no_obj = conn.execute(text("""
            SELECT c.id FROM controls c
            LEFT JOIN assessment_objectives ao ON c.id = ao.control_id
            WHERE ao.id IS NULL
        """)).fetchall()
        check("All controls have objectives", len(no_obj) == 0,
              f"{len(no_obj)} controls without objectives")


def verify_qdrant():
    """Check Qdrant collection and RAG retrieval."""
    print("\n" + "=" * 60)
    print("2. QDRANT VERIFICATION")
    print("=" * 60)

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    embedding_svc = get_embedding_service()

    # Collection exists
    collections = [c.name for c in client.get_collections().collections]
    check("Collection exists", COLLECTION_NAME in collections)

    if COLLECTION_NAME not in collections:
        print("  Skipping Qdrant tests — collection not found")
        return

    info = client.get_collection(COLLECTION_NAME)
    check("Points loaded", info.points_count > 0,
          f"{info.points_count} points")
    check("Expected chunk count", info.points_count >= 360,
          f"expected ~370, got {info.points_count}")

    # --- RAG Query 1: Specific control lookup ---
    print("\n  --- RAG Query: 'What does AC.L2-3.1.1 require?' ---")
    q = embedding_svc.embed_query("What does AC.L2-3.1.1 require?")
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=q,
        limit=3,
        with_payload=True,
    ).points
    top_hit = results[0].payload if results else {}
    check("Q1 returns results", len(results) > 0)
    check("Q1 top hit is AC control",
          top_hit.get("control_id", "").startswith("AC.L2-3.1.1"),
          f"got control_id={top_hit.get('control_id')}")
    check("Q1 relevance score > 0.5", results[0].score > 0.5 if results else False,
          f"score={results[0].score:.4f}" if results else "no results")

    for i, r in enumerate(results):
        print(f"    [{i+1}] score={r.score:.4f} type={r.payload.get('type')} "
              f"ctrl={r.payload.get('control_id', '—')}")

    # --- RAG Query 2: Topic-based search ---
    print("\n  --- RAG Query: 'multifactor authentication' ---")
    q = embedding_svc.embed_query("multifactor authentication requirements")
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=q,
        limit=3,
        with_payload=True,
    ).points
    check("Q2 returns results", len(results) > 0)
    hit_ids = [r.payload.get("control_id", "") for r in results]
    check("Q2 finds MFA control (IA.L2-3.5.3)",
          any("3.5.3" in cid for cid in hit_ids),
          f"got: {hit_ids}")

    for i, r in enumerate(results):
        print(f"    [{i+1}] score={r.score:.4f} type={r.payload.get('type')} "
              f"ctrl={r.payload.get('control_id', '—')}")

    # --- RAG Query 3: Filtered search by family ---
    print("\n  --- Filtered search: family_id=SC ---")
    q = embedding_svc.embed_query("encryption CUI protection")
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=q,
        query_filter=Filter(
            must=[FieldCondition(
                key="family_id",
                match=MatchValue(value="SC"),
            )]
        ),
        limit=3,
        with_payload=True,
    ).points
    check("Filtered search returns results", len(results) > 0)
    all_sc = all(r.payload.get("family_id") == "SC" for r in results)
    check("All results from SC family", all_sc)

    for i, r in enumerate(results):
        print(f"    [{i+1}] score={r.score:.4f} "
              f"ctrl={r.payload.get('control_id', '—')} "
              f"family={r.payload.get('family_id')}")

    # --- RAG Query 4: Objective search for evidence mapping ---
    print("\n  --- Objective search: 'evidence for access control audit' ---")
    q = embedding_svc.embed_query("evidence needed for access control audit assessment")
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=q,
        query_filter=Filter(
            must=[FieldCondition(
                key="type",
                match=MatchValue(value="objective"),
            )]
        ),
        limit=3,
        with_payload=True,
    ).points
    check("Objective search returns results", len(results) > 0)
    all_objectives = all(
        r.payload.get("type") == "objective" for r in results
    )
    check("All results are objectives", all_objectives)

    for i, r in enumerate(results):
        print(f"    [{i+1}] score={r.score:.4f} "
              f"obj={r.payload.get('objective_id', '—')} "
              f"ctrl={r.payload.get('control_id', '—')}")


def main():
    print("=" * 60)
    print("WEEK 2 STEP 2 — END-TO-END VERIFICATION")
    print("=" * 60)

    verify_postgres()
    verify_qdrant()

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    print("\nIf all checks passed, Week 2 Step 2 is done!")
    print("Next: Week 3 — SSP Generation Agent")


if __name__ == "__main__":
    main()