"""
POA&M (Plan of Action & Milestones) Auto-Generator.

For controls scored as NOT MET or PARTIAL, auto-generates POA&M items
in the poam_items table with 180-day remediation deadlines.

Rules:
- CA.L2-3.12.4 (System Security Plan) CANNOT be placed on POA&M
- Only controls with poam_eligible=True in the controls table can have POA&M items
- Deadline is 180 days from creation (CMMC requirement)
- Existing active POA&M items for the same control are not duplicated

Actual poam_items columns:
  id, org_id, control_id, weakness_description, remediation_plan,
  milestone_changes (json), resources_required, scheduled_completion,
  actual_completion, status (poam_status enum: OPEN/IN_PROGRESS/CLOSED/OVERDUE),
  risk_level, created_at, updated_at
"""

import sys
import os
import json
import hashlib
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import text
from src.db.session import get_session


def _generate_id(prefix: str = "poam") -> str:
    import time
    import random
    seed = f"{time.time()}-{random.randint(0, 99999)}"
    return f"{prefix}-{hashlib.sha256(seed.encode()).hexdigest()[:8]}"


def _log_audit(session, actor: str, action: str, target_type: str,
               target_id: str, details: dict):
    # Delegate to the canonical writer so the hash algorithm matches
    # src/evidence/state_machine.py::_compute_entry_hash exactly.
    # Otherwise verify_audit_chain rejects the entry.
    from src.evidence.state_machine import create_audit_entry
    create_audit_entry(
        db=session,
        actor=actor,
        actor_type="SYSTEM",
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )


class POAMGenerator:
    """
    Auto-generate POA&M items for non-compliant controls.

    Usage:
        gen = POAMGenerator(org_id="9de53b587b23450b87af")
        created, skipped = gen.generate_from_ssp()
    """

    FORBIDDEN_CONTROLS = {"CA.L2-3.12.4"}  # SSP cannot be on POA&M
    DEFAULT_DEADLINE_DAYS = 180

    def __init__(self, org_id: str, actor: str = "poam-generator"):
        self.org_id = org_id
        self.actor = actor

    def _risk_from_points(self, points: int) -> str:
        if points >= 5:
            return "HIGH"
        elif points >= 3:
            return "MODERATE"
        return "LOW"

    def generate_from_ssp(self) -> tuple:
        """
        Scan ssp_sections for NOT MET / PARTIAL controls and create POA&M items.
        Returns (created_count, skipped_count).
        """
        created = 0
        skipped = 0

        with get_session() as session:
            rows = session.execute(text("""
                SELECT c.id, c.title, c.points, c.poam_eligible,
                       s.implementation_status
                FROM controls c
                JOIN ssp_sections s ON c.id = s.control_id AND s.org_id = :org_id
                WHERE s.implementation_status IN ('Not Implemented', 'Partially Implemented')
                ORDER BY c.points DESC, c.id
            """), {"org_id": self.org_id}).fetchall()

            # Existing active POA&M items (OPEN or IN_PROGRESS)
            existing = set()
            existing_rows = session.execute(text("""
                SELECT control_id FROM poam_items
                WHERE org_id = :org_id
                AND status IN ('OPEN', 'IN_PROGRESS')
            """), {"org_id": self.org_id}).fetchall()
            for er in existing_rows:
                existing.add(er[0])

            now = datetime.utcnow()
            deadline = now + timedelta(days=self.DEFAULT_DEADLINE_DAYS)

            for row in rows:
                control_id, title, points, poam_eligible, impl_status = row

                if control_id in self.FORBIDDEN_CONTROLS:
                    print(f"  BLOCKED: {control_id} cannot be placed on POA&M (SSP requirement)")
                    skipped += 1
                    continue

                if not poam_eligible:
                    print(f"  BLOCKED: {control_id} is not POA&M eligible")
                    skipped += 1
                    continue

                if control_id in existing:
                    print(f"  SKIP: {control_id} already has an active POA&M item")
                    skipped += 1
                    continue

                poam_id = _generate_id("poam")
                weakness = (
                    f"Control {control_id} ({title}) is assessed as {impl_status}. "
                    f"This is a {points}-point control requiring remediation."
                )
                remediation = (
                    f"1. Review current implementation gaps for {control_id}\n"
                    f"2. Develop remediation plan with resource allocation\n"
                    f"3. Implement required technical/administrative controls\n"
                    f"4. Collect and publish evidence artifacts\n"
                    f"5. Update SSP narrative to reflect implementation"
                )
                milestones = json.dumps([
                    {"step": 1, "description": "Gap analysis complete", "target_days": 30},
                    {"step": 2, "description": "Remediation plan approved", "target_days": 60},
                    {"step": 3, "description": "Implementation complete", "target_days": 120},
                    {"step": 4, "description": "Evidence collected and published", "target_days": 150},
                    {"step": 5, "description": "SSP narrative updated", "target_days": 180},
                ])
                risk_level = self._risk_from_points(points)

                # Uses actual poam_items columns
                session.execute(text("""
                    INSERT INTO poam_items (
                        id, org_id, control_id, weakness_description,
                        remediation_plan, milestone_changes, resources_required,
                        scheduled_completion, status, risk_level,
                        created_at, updated_at
                    ) VALUES (
                        :id, :org_id, :control_id, :weakness_description,
                        :remediation_plan, CAST(:milestone_changes AS json),
                        :resources_required,
                        :scheduled_completion, 'OPEN', :risk_level,
                        :created_at, :updated_at
                    )
                """), {
                    "id": poam_id,
                    "org_id": self.org_id,
                    "control_id": control_id,
                    "weakness_description": weakness,
                    "remediation_plan": remediation,
                    "milestone_changes": milestones,
                    "resources_required": f"IT security staff, budget for {control_id} remediation",
                    "scheduled_completion": deadline,
                    "risk_level": risk_level,
                    "created_at": now,
                    "updated_at": now,
                })

                _log_audit(session, self.actor, "POAM_CREATED", "poam_item", poam_id, {
                    "org_id": self.org_id,
                    "control_id": control_id,
                    "risk_level": risk_level,
                    "deadline": deadline.date().isoformat(),
                    "impl_status": impl_status,
                })

                created += 1
                print(f"  CREATED: {poam_id} for {control_id} "
                      f"({points}pt, {risk_level} risk, deadline {deadline.date().isoformat()})")

            session.commit()

        return created, skipped

    def get_poam_summary(self) -> dict:
        with get_session() as session:
            rows = session.execute(text("""
                SELECT
                    p.id, p.control_id, p.weakness_description, p.status::text,
                    p.scheduled_completion, p.risk_level,
                    c.title, c.family_abbrev, c.points,
                    p.remediation_plan, p.milestone_changes
                FROM poam_items p
                JOIN controls c ON c.id = p.control_id
                WHERE p.org_id = :org_id
                ORDER BY c.points DESC, p.control_id
            """), {"org_id": self.org_id}).fetchall()

        total_points_at_risk = 0
        items = []
        status_counts = {"OPEN": 0, "IN_PROGRESS": 0, "CLOSED": 0, "OVERDUE": 0}

        for row in rows:
            pid, cid, weakness, status, deadline, risk, title, fam, points, \
                remediation_plan, milestone_changes = row
            items.append({
                "poam_id": pid,
                "control_id": cid,
                "family": fam,
                "title": title,
                "status": status,
                "points": points,
                "risk_level": risk,
                "deadline": str(deadline) if deadline else None,
                "weakness": weakness,
                "remediation_plan": remediation_plan,
                "milestone_changes": milestone_changes,
            })
            status_counts[status] = status_counts.get(status, 0) + 1
            if status in ("OPEN", "IN_PROGRESS"):
                total_points_at_risk += points

        return {
            "total_items": len(items),
            "status_counts": status_counts,
            "total_points_at_risk": total_points_at_risk,
            "items": items,
        }


if __name__ == "__main__":
    org_id = sys.argv[1] if len(sys.argv) > 1 else "9de53b587b23450b87af"
    gen = POAMGenerator(org_id=org_id)

    print(f"\nGenerating POA&M items for org {org_id}...")
    created, skipped = gen.generate_from_ssp()
    print(f"\nDone: {created} created, {skipped} skipped")

    summary = gen.get_poam_summary()
    print(f"\nPOA&M Summary:")
    print(f"  Total items: {summary['total_items']}")
    print(f"  Points at risk: {summary['total_points_at_risk']}")
    print(f"  Status: {summary['status_counts']}")
