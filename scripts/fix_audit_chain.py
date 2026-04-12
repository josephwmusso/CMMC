"""
Fix a broken audit_log chain by recomputing entry_hash for every row
using the same algorithm as src/evidence/state_machine.py::verify_audit_chain.

The chain is rebuilt forward from the genesis entry:
  - Entry #1 (genesis): prev_hash stays "GENESIS"
  - For each entry in id ASC order:
      - entry_hash = sha256(json.dumps({...all fields...}, sort_keys=True))
      - next entry's prev_hash = this entry_hash

Preserves all row data. Updates only prev_hash and entry_hash columns.

Usage:
  python scripts/fix_audit_chain.py --dry-run                         # preview
  python scripts/fix_audit_chain.py --execute                         # apply
  python scripts/fix_audit_chain.py --database-url <url> --dry-run    # remote preview
  python scripts/fix_audit_chain.py --database-url <url> --execute    # remote apply
"""
import argparse
import hashlib
import json
import os
import sys

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
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Show changes without applying (default)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually apply the fixes")
    args = parser.parse_args()

    # --execute overrides --dry-run
    apply_changes = args.execute

    import psycopg2
    import psycopg2.extras

    url = get_db_url(args)
    print(f"Connecting to: {url.split('@')[-1] if '@' in url else url}")
    print(f"Mode: {'EXECUTE (will modify DB)' if apply_changes else 'DRY RUN (read-only)'}")
    print()

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

    if not rows:
        print("No entries — nothing to fix.")
        conn.close()
        return

    print(f"Walking {len(rows)} entries...\n")

    updates = []  # list of (id, new_prev, new_hash)
    expected_prev = "GENESIS"

    for row in rows:
        rid = row["id"]
        actor = row["actor"]
        actor_type = row["actor_type"]
        action = row["action"]
        ttype = row["target_type"]
        tid = row["target_id"]
        details = row["details"]
        old_prev = row["prev_hash"]
        old_hash = row["entry_hash"]
        ts = row["timestamp"]

        # Normalize details to dict (verifier does this too)
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

        new_prev = expected_prev
        new_hash = compute_entry_hash(
            actor=actor, actor_type=actor_type, action=action,
            target_type=ttype, target_id=tid,
            details=details_dict, prev_hash=new_prev, timestamp=ts_iso,
        )

        prev_changed = (old_prev != new_prev)
        hash_changed = (old_hash != new_hash)

        if prev_changed or hash_changed:
            updates.append((rid, new_prev, new_hash, old_prev, old_hash))
            marker = "FIX"
        else:
            marker = "ok"

        print(f"  [{marker:3}] id={rid:<4} action={str(action)[:18]:<18} "
              f"prev:{str(old_prev)[:12]}->{new_prev[:12]}  "
              f"hash:{str(old_hash)[:12]}->{new_hash[:12]}")

        expected_prev = new_hash

    print()
    print(f"Entries to fix: {len(updates)} / {len(rows)}")

    if not updates:
        print("Chain is already intact. No changes needed.")
        conn.close()
        return

    if not apply_changes:
        print()
        print("DRY RUN — no changes applied.")
        print(f"Run with --execute to apply {len(updates)} update(s).")
        conn.close()
        return

    # Apply updates
    print()
    print(f"Applying {len(updates)} updates...")
    cur2 = conn.cursor()
    for rid, new_prev, new_hash, _, _ in updates:
        cur2.execute(
            "UPDATE audit_log SET prev_hash = %s, entry_hash = %s WHERE id = %s",
            (new_prev, new_hash, rid),
        )
    conn.commit()
    conn.close()
    print(f"Applied {len(updates)} updates. Chain should now be intact.")
    print(f"Verify: curl <base_url>/api/evidence/audit/verify")


if __name__ == "__main__":
    main()
