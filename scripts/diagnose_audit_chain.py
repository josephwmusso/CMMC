"""
Diagnose audit chain integrity.

Walks every audit_log entry, recomputes the expected entry_hash using the
EXACT same algorithm as src/evidence/state_machine.py::_compute_entry_hash,
and compares against the stored value.

Usage:
  python scripts/diagnose_audit_chain.py                           # local
  python scripts/diagnose_audit_chain.py --database-url <url>      # remote
"""
import argparse
import hashlib
import json
import os
import sys
from typing import Any

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def compute_entry_hash(actor, actor_type, action, target_type, target_id,
                      details, prev_hash, timestamp) -> str:
    """EXACT copy of src/evidence/state_machine.py::_compute_entry_hash."""
    payload = json.dumps(
        {
            "actor": actor,
            "actor_type": actor_type,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "details": details,
            "prev_hash": prev_hash,
            "timestamp": timestamp,
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_db_url(args) -> str:
    if args.database_url:
        return args.database_url
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        url = "postgresql://cmmc:localdev@localhost:5432/cmmc"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url",
                        help="Postgres connection string (overrides DATABASE_URL env var)")
    args = parser.parse_args()

    import psycopg2
    import psycopg2.extras

    url = get_db_url(args)
    print(f"Connecting to: {url.split('@')[-1] if '@' in url else url}")

    try:
        conn = psycopg2.connect(url)
    except Exception as e:
        print(f"ERROR: Could not connect: {e}")
        sys.exit(1)

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT id, actor, actor_type, action, target_type, target_id,
               details, prev_hash, entry_hash, timestamp
        FROM audit_log
        ORDER BY id ASC
    """)
    rows = cur.fetchall()
    conn.close()

    print(f"\nTotal entries: {len(rows)}\n")
    if not rows:
        print("No entries — nothing to diagnose.")
        return

    print(f"{'id':<5} {'actor':<12} {'action':<20} {'prev_hash':<20} {'entry_hash':<20} {'recomputed':<20} {'match':<6}")
    print("-" * 115)

    expected_prev = "GENESIS"
    first_break = None

    for row in rows:
        rid = row["id"]
        actor = row["actor"]
        actor_type = row["actor_type"]
        action = row["action"]
        ttype = row["target_type"]
        tid = row["target_id"]
        details = row["details"]
        prev = row["prev_hash"]
        stored = row["entry_hash"]
        ts = row["timestamp"]

        # Normalize details to dict
        if isinstance(details, str):
            try:
                details_dict = json.loads(details)
            except Exception:
                details_dict = {}
        elif details is None:
            details_dict = {}
        else:
            details_dict = details

        ts_iso = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)

        recomputed = compute_entry_hash(
            actor=actor, actor_type=actor_type, action=action,
            target_type=ttype, target_id=tid,
            details=details_dict, prev_hash=prev, timestamp=ts_iso,
        )

        chain_ok = (prev == expected_prev)
        hash_ok = (recomputed == stored)
        status = "OK" if (chain_ok and hash_ok) else "BREAK"

        print(f"{rid:<5} {str(actor)[:12]:<12} {str(action)[:20]:<20} "
              f"{str(prev)[:18]:<20} {str(stored)[:18]:<20} "
              f"{recomputed[:18]:<20} {status:<6}")

        if first_break is None and not (chain_ok and hash_ok):
            first_break = rid
            if not chain_ok:
                print(f"      ^^ prev_hash mismatch: stored={prev[:20]}... expected={expected_prev[:20]}...")
            if not hash_ok:
                print(f"      ^^ entry_hash mismatch: stored={stored[:20]}... recomputed={recomputed[:20]}...")
                print(f"      ^^ Seeder likely used a different hash algorithm than the verifier.")
                # Show what the seeder wrote:
                seeder_hash = hashlib.sha256("GENESIS".encode()).hexdigest()
                if stored == seeder_hash:
                    print(f"      ^^ CONFIRMED: stored hash == sha256('GENESIS'). "
                          f"Seeder wrote the wrong hash — it should be sha256(json_payload).")

        expected_prev = stored  # verifier advances chain regardless of match

    print()
    if first_break is None:
        print("Chain is INTACT. No breaks detected.")
        sys.exit(0)
    else:
        print(f"Chain BROKEN at entry id={first_break}")
        print(f"Run: python scripts/fix_audit_chain.py --dry-run  # preview fix")
        print(f"Run: python scripts/fix_audit_chain.py --execute  # apply fix")
        sys.exit(1)


if __name__ == "__main__":
    main()
