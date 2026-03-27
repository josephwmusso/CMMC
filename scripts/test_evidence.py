"""
End-to-end test for the evidence hashing + state machine pipeline.
Run: python -m scripts.test_evidence
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from configs.settings import DATABASE_URL, EVIDENCE_DIR

from src.evidence.hasher import hash_file, hash_artifact, verify_hash
from src.evidence.storage import upload_evidence, get_artifact, list_artifacts
from src.evidence.state_machine import (
    transition_evidence,
    StateTransitionError,
    verify_audit_chain,
)

ORG_ID = "9de53b587b23450b87af"


def main():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            print(f"  [PASS] {name}")
            passed += 1
        else:
            print(f"  [FAIL] {name}")
            failed += 1

    # ── 1. Hasher tests ──────────────────────────────────────────────
    print("\n=== 1. HASHER TESTS ===")

    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    test_file = os.path.join(EVIDENCE_DIR, "_test_hash.txt")
    with open(test_file, "w") as f:
        f.write("This is test evidence content for SHA-256 hashing.")

    h = hash_file(test_file)
    check("hash_file returns 64-char hex", len(h) == 64)
    check("hash_file is deterministic", hash_file(test_file) == h)

    meta = hash_artifact(test_file)
    check("hash_artifact returns sha256", meta["sha256"] == h)
    check("hash_artifact has filename", meta["filename"] == "_test_hash.txt")

    check("verify_hash correct", verify_hash(test_file, h))
    check("verify_hash rejects bad hash", not verify_hash(test_file, "bad" * 16))

    os.remove(test_file)

    # ── 2. Upload test ───────────────────────────────────────────────
    print("\n=== 2. UPLOAD TEST ===")

    sample_content = b"Access Control Policy v2.1\nApex Defense Solutions\nEffective: 2026-01-15"

    result = upload_evidence(
        db=db,
        org_id=ORG_ID,
        filename="access_control_policy.pdf",
        file_bytes=sample_content,
        uploaded_by="test-runner",
        description="AC policy document for testing",
        source_system="manual",
        evidence_dir=EVIDENCE_DIR,
    )
    artifact_id = result["artifact_id"]

    check("upload returns artifact_id", artifact_id.startswith("EVD-"))
    check("upload state is draft", result["state"] == "draft")
    check("file size correct", result["file_size"] == len(sample_content))

    fetched = get_artifact(db, artifact_id)
    check("get_artifact works", fetched is not None)
    check("stored state is DRAFT", fetched["state"] == "DRAFT")
    check("file exists on disk", os.path.exists(fetched["file_path"]))

    # ── 3. State machine tests ───────────────────────────────────────
    print("\n=== 3. STATE MACHINE TESTS ===")

    r = transition_evidence(db, artifact_id, "reviewed", "reviewer-1", "Looks good")
    check("DRAFT->REVIEWED succeeds", r["new_state"] == "REVIEWED")

    r = transition_evidence(db, artifact_id, "approved", "approver-1", "Approved for publish")
    check("REVIEWED->APPROVED succeeds", r["new_state"] == "APPROVED")

    r = transition_evidence(db, artifact_id, "published", "publisher-1", "Final")
    check("APPROVED->PUBLISHED succeeds", r["new_state"] == "PUBLISHED")
    check("published has sha256_hash", r["sha256_hash"] is not None and len(r["sha256_hash"]) == 64)

    pub = get_artifact(db, artifact_id)
    check("DB hash matches file", verify_hash(pub["file_path"], pub["sha256_hash"]))

    try:
        transition_evidence(db, artifact_id, "draft", "attacker")
        check("published is immutable", False)
    except StateTransitionError:
        check("published is immutable", True)

    # ── 4. Invalid transitions ───────────────────────────────────────
    print("\n=== 4. INVALID TRANSITION TESTS ===")

    result2 = upload_evidence(
        db=db, org_id=ORG_ID, filename="test_invalid.txt",
        file_bytes=b"test", uploaded_by="test", evidence_dir=EVIDENCE_DIR,
    )
    aid2 = result2["artifact_id"]

    try:
        transition_evidence(db, aid2, "approved", "test")
        check("DRAFT->APPROVED blocked", False)
    except StateTransitionError:
        check("DRAFT->APPROVED blocked", True)

    try:
        transition_evidence(db, aid2, "published", "test")
        check("DRAFT->PUBLISHED blocked", False)
    except StateTransitionError:
        check("DRAFT->PUBLISHED blocked", True)

    transition_evidence(db, aid2, "reviewed", "test")
    r = transition_evidence(db, aid2, "draft", "test", "Needs rework")
    check("REVIEWED->DRAFT send-back works", r["new_state"] == "DRAFT")

    # ── 5. Audit chain verification ──────────────────────────────────
    print("\n=== 5. AUDIT CHAIN VERIFICATION ===")

    chain = verify_audit_chain(db)
    check("audit chain is valid", chain["valid"])
    check("audit chain has entries", chain["entries_checked"] > 0)
    print(f"       Entries verified: {chain['entries_checked']}")

    # ── 6. List artifacts ────────────────────────────────────────────
    print("\n=== 6. LIST & FILTER ===")

    all_arts = list_artifacts(db, ORG_ID)
    check("list returns artifacts", len(all_arts) >= 2)

    pub_arts = list_artifacts(db, ORG_ID, state="PUBLISHED")
    check("filter by published works", all(a["state"] == "PUBLISHED" for a in pub_arts))

    # ── Summary ──────────────────────────────────────────────────────
    print(f"\n{'='*50}")
    print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed}")
    if failed == 0:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED - check output above")
    print(f"{'='*50}")

    db.close()


if __name__ == "__main__":
    main()