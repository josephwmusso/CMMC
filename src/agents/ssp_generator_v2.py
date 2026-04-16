"""
src/agents/ssp_generator_v2.py
Evidence-gated SSP generator.
"""

import json
import re
import hashlib
from datetime import datetime, timezone

from sqlalchemy import text

from src.agents.llm_client import get_llm
from src.agents.ssp_prompts_v2 import (
    SSP_SYSTEM_PROMPT,
    build_user_prompt,
)
from src.agents.ssp_schemas import SSPSectionOutput, ImplementationStatus
from src.agents.hallucination_detector import run_verification
from src.db.session import get_session
from src.utils.service_check import is_qdrant_available
import configs.settings as settings


# =============================================================================
# Backward-compat aliases for code that imports from ssp_generator (v1 name)
# =============================================================================
from dataclasses import dataclass, field as dc_field


@dataclass
class SSPControlResult:
    """Backward-compatible dataclass matching the old ssp_generator.SSPControlResult interface."""
    control_id: str = ""
    status: str = "Not Assessed"
    narrative: str = ""
    evidence_artifacts: list = dc_field(default_factory=list)
    gaps: list = dc_field(default_factory=list)
    error: str = ""
    generation_time_sec: float = 0.0
    db_artifact_refs: list = dc_field(default_factory=list)


class SSPGeneratorV2:
    """Evidence-gated SSP section generator."""

    def __init__(self, org_profile: dict):
        if not org_profile or not org_profile.get("name"):
            raise ValueError(
                "SSPGeneratorV2 requires a populated org_profile dict. "
                "Use build_org_profile(org_id, db) to construct it."
            )
        self.org_profile = org_profile
        self.org_id = self.org_profile.get("org_id", "default-org")
        self.llm = get_llm()
        self._qdrant = None
        self.collection = settings.QDRANT_COLLECTION

    @property
    def qdrant(self):
        """Lazy Qdrant client — only connects when actually used."""
        if self._qdrant is None:
            from qdrant_client import QdrantClient
            self._qdrant = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        return self._qdrant

    def get_control_context(self, control_id: str) -> tuple[str, str, str, int, bool]:
        """
        Retrieve control description and objectives.
        Uses Qdrant when available, falls back to Postgres.
        Returns (control_title, control_description, objectives_text, sprs_points, poam_eligible).
        """
        if is_qdrant_available():
            return self._get_context_from_qdrant(control_id)
        return self._get_context_from_postgres(control_id)

    def _get_context_from_qdrant(self, control_id: str) -> tuple[str, str, str, int, bool]:
        """Qdrant path — original implementation."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        control_results = self.qdrant.scroll(
            collection_name=self.collection,
            scroll_filter=Filter(must=[
                FieldCondition(key="control_id", match=MatchValue(value=control_id)),
                FieldCondition(key="type", match=MatchValue(value="control")),
            ]),
            limit=1,
        )[0]

        if not control_results:
            raise ValueError(f"Control {control_id} not found in Qdrant")

        payload = control_results[0].payload
        control_title = payload.get("title", control_id)
        control_description = payload.get("text", "")
        sprs_points = payload.get("points", 1)
        poam_eligible = payload.get("poam_eligible", True)

        objective_results = self.qdrant.scroll(
            collection_name=self.collection,
            scroll_filter=Filter(must=[
                FieldCondition(key="control_id", match=MatchValue(value=control_id)),
                FieldCondition(key="type", match=MatchValue(value="objective")),
            ]),
            limit=20,
        )[0]

        objectives_lines = []
        for obj in objective_results:
            obj_id = obj.payload.get("objective_id", "?")
            obj_text = obj.payload.get("text", "")
            objectives_lines.append(f"[{obj_id}] {obj_text}")

        objectives_text = "\n\n".join(objectives_lines) if objectives_lines else "No objectives found."
        return control_title, control_description, objectives_text, sprs_points, poam_eligible

    def _get_context_from_postgres(self, control_id: str) -> tuple[str, str, str, int, bool]:
        """Postgres fallback — same data, SQL instead of vector scroll."""
        with get_session() as session:
            row = session.execute(text(
                "SELECT title, description, discussion, points, poam_eligible "
                "FROM controls WHERE id = :cid"
            ), {"cid": control_id}).fetchone()

            if not row:
                raise ValueError(f"Control {control_id} not found in database")

            control_title = row[0]
            # Combine description + discussion for full context (matches what Qdrant stores as "text")
            control_description = row[1] or ""
            if row[2]:
                control_description += f"\n\nDiscussion: {row[2]}"
            sprs_points = row[3] or 1
            poam_eligible = row[4] if row[4] is not None else True

            # Get assessment objectives
            obj_rows = session.execute(text(
                "SELECT id, description, examine, interview, test "
                "FROM assessment_objectives WHERE control_id = :cid ORDER BY id"
            ), {"cid": control_id}).fetchall()

            objectives_lines = []
            for obj in obj_rows:
                obj_text = obj[1] or ""
                if obj[2]:
                    obj_text += f" Examine: {obj[2]}"
                if obj[3]:
                    obj_text += f" Interview: {obj[3]}"
                if obj[4]:
                    obj_text += f" Test: {obj[4]}"
                objectives_lines.append(f"[{obj[0]}] {obj_text}")

            objectives_text = "\n\n".join(objectives_lines) if objectives_lines else "No objectives found."
            return control_title, control_description, objectives_text, sprs_points, poam_eligible

    def get_linked_evidence(self, control_id: str) -> list[dict]:
        """
        Query Postgres for evidence artifacts linked to a specific control.
        Returns list of evidence dicts with id, filename (as title), state, etc.
        """
        query = text("""
            SELECT
                ea.id,
                ea.filename,
                ea.evidence_type,
                ea.source_system,
                ea.description,
                ea.state,
                ea.sha256_hash,
                ea.file_size_bytes,
                ea.owner
            FROM evidence_artifacts ea
            JOIN evidence_control_map ecm ON ecm.evidence_id = ea.id
            WHERE ecm.control_id = :control_id
              AND ea.org_id = :org_id
            ORDER BY ea.state DESC, ea.filename
        """)

        with get_session() as session:
            rows = session.execute(query, {
                "control_id": control_id,
                "org_id": self.org_id,
            }).fetchall()

        evidence = []
        for row in rows:
            evidence.append({
                "id": row[0],
                "title": row[1],          # filename used as title
                "evidence_type": row[2],
                "source_system": row[3],
                "description": row[4],
                "state": row[5],
                "sha256_hash": row[6],
                "file_size_bytes": row[7],
                "owner": row[8],
            })

        return evidence

    def generate_section(self, control_id: str) -> dict:
        """
        Generate a single SSP section with evidence gating and verification.

        Returns dict with:
            - parsed: The validated SSPSectionOutput as dict
            - verification: VerificationResult
            - raw_response: The raw LLM response string
            - evidence_count: Number of linked evidence artifacts
            - generation_mode: "evidenced", "partial", or "gap_report"
        """
        # Step 1: Get control context from Qdrant (includes points + poam_eligible)
        control_title, control_description, objectives_text, sprs_points, poam_eligible = \
            self.get_control_context(control_id)

        # Step 2: Get linked evidence from Postgres
        evidence = self.get_linked_evidence(control_id)

        # Determine generation mode for logging
        published_evidence = [e for e in evidence if e.get("state", "").upper() == "PUBLISHED"]
        if published_evidence:
            generation_mode = "evidenced"
        elif evidence:
            generation_mode = "partial"
        else:
            generation_mode = "gap_report"

        # Step 3: Build prompt
        user_prompt = build_user_prompt(
            control_id=control_id,
            control_title=control_title,
            control_description=control_description,
            objectives_text=objectives_text,
            sprs_points=sprs_points,
            poam_eligible=poam_eligible,
            evidence_artifacts=evidence,
            org_profile=self.org_profile,
        )

        # Step 4: Call LLM
        raw_response = self.llm.generate(
            system_prompt=SSP_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=4096,
        )

        # Step 5: Parse response into structured output
        parsed = self._parse_response(raw_response, control_id)

        # Step 6: Run hallucination verification
        verification = run_verification(
            control_id=control_id,
            parsed_output=parsed,
            evidence_artifacts=evidence,
            org_profile=self.org_profile,
        )

        # Step 7: If verification fails with critical findings, convert to gap report
        if not verification.passed:
            print(f"  WARNING: {control_id}: Hallucination detected - converting to gap report")
            for finding in verification.findings:
                if finding.severity == "critical":
                    print(f"     [{finding.finding_type}] {finding.value}")

            parsed = self._convert_to_gap_report(
                control_id=control_id,
                control_title=control_title,
                original_parsed=parsed,
                verification=verification,
                sprs_points=sprs_points,
            )
            generation_mode = "gap_report_auto"

        return {
            "parsed": parsed,
            "verification": verification,
            "raw_response": raw_response,
            "evidence_count": len(evidence),
            "generation_mode": generation_mode,
        }

    def _parse_response(self, raw: str, control_id: str) -> dict:
        """Parse LLM JSON response. Falls back to gap report on parse failure."""
        cleaned = raw.strip()
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)

        try:
            data = json.loads(cleaned)
            validated = SSPSectionOutput(**data)
            return validated.model_dump()
        except (json.JSONDecodeError, Exception) as e:
            print(f"  WARNING: {control_id}: Parse error - {e}")
            return {
                "control_id": control_id,
                "control_title": control_id,
                "implementation_status": "Not Implemented",
                "narrative": (
                    f"{control_id} - EVIDENCE GAP REPORT\n\n"
                    f"Current State: Unable to generate structured assessment. "
                    f"The AI response could not be parsed into the required format.\n\n"
                    f"Evidence Needed: Evidence artifacts must be linked to this control "
                    f"before a valid implementation narrative can be generated.\n\n"
                    f"Recommended Actions: Upload relevant evidence and re-generate."
                ),
                "evidence_references": [],
                "gaps": [{
                    "gap_type": "missing_evidence",
                    "description": f"No valid assessment generated for {control_id}",
                    "remediation": "Link evidence artifacts and re-generate SSP section",
                    "sprs_impact": 1,
                }],
                "assessment_objectives_met": [],
                "assessment_objectives_not_met": [],
            }

    def _convert_to_gap_report(
        self,
        control_id: str,
        control_title: str,
        original_parsed: dict,
        verification,
        sprs_points: int,
    ) -> dict:
        """
        When verification detects hallucination, replace the narrative
        with an honest gap report preserving any valid evidence refs.
        """
        finding_lines = []
        for f in verification.findings:
            if f.severity == "critical":
                finding_lines.append(
                    f"- Fabricated {f.finding_type}: {f.value}"
                )

        findings_text = "\n".join(finding_lines) if finding_lines else "Unverifiable claims detected."

        gap_narrative = (
            f"{control_title} - EVIDENCE GAP REPORT\n\n"
            f"Current State: An implementation narrative was generated but failed "
            f"integrity verification. The following fabricated details were detected:\n"
            f"{findings_text}\n\n"
            f"Evidence Needed: Specific evidence artifacts must be linked to this control "
            f"to support implementation claims. Without linked evidence, the platform "
            f"cannot generate verifiable narratives.\n\n"
            f"Recommended Actions:\n"
            f"1. Upload evidence artifacts relevant to {control_id}\n"
            f"2. Link artifacts to this control via the Evidence page\n"
            f"3. Walk artifacts through review pipeline to PUBLISHED state\n"
            f"4. Re-generate SSP section with linked evidence"
        )

        return {
            "control_id": control_id,
            "control_title": control_title,
            "implementation_status": "Not Implemented",
            "narrative": gap_narrative,
            "evidence_references": [],
            "gaps": [{
                "gap_type": "missing_evidence",
                "description": (
                    f"Implementation narrative contained fabricated details "
                    f"({verification.critical_count} critical findings). "
                    f"Evidence must be linked before claims can be made."
                ),
                "remediation": f"Link and publish evidence for {control_id}, then re-generate.",
                "sprs_impact": sprs_points,
            }],
            "assessment_objectives_met": [],
            "assessment_objectives_not_met": original_parsed.get("assessment_objectives_not_met", []),
        }

    def persist_section(self, parsed: dict, version: int = 1) -> str:
        """
        Persist a generated section to the ssp_sections table.
        Uses raw SQL with CAST(:x AS json).
        Returns the section ID.
        """
        control_id = parsed["control_id"]
        now = datetime.now(timezone.utc)

        seed = f"{self.org_id}:{control_id}:{version}"
        section_id = hashlib.sha256(seed.encode()).hexdigest()[:20]

        status = parsed["implementation_status"]

        evidence_refs = json.dumps(parsed.get("evidence_references", []))
        gaps = json.dumps(parsed.get("gaps", []))

        query = text("""
            INSERT INTO ssp_sections
                (id, org_id, control_id, implementation_status, narrative,
                 evidence_refs, gaps, version, generated_by, created_at, updated_at)
            VALUES
                (:id, :org_id, :control_id, :status, :narrative,
                 CAST(:evidence_refs AS json), CAST(:gaps AS json),
                 :version, :generated_by, :created_at, :updated_at)
            ON CONFLICT (org_id, control_id, version) DO UPDATE SET
                implementation_status = :status,
                narrative = :narrative,
                evidence_refs = CAST(:evidence_refs AS json),
                gaps = CAST(:gaps AS json),
                generated_by = :generated_by,
                updated_at = :updated_at
        """)

        with get_session() as session:
            session.execute(query, {
                "id": section_id,
                "org_id": self.org_id,
                "control_id": control_id,
                "status": status,
                "narrative": parsed["narrative"],
                "evidence_refs": evidence_refs,
                "gaps": gaps,
                "version": version,
                "generated_by": "ssp_generator_v2",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            })
            session.commit()

        return section_id


def test_single_control(control_id: str = "AC.L2-3.1.1"):
    """Quick test: generate one control and print results."""
    gen = SSPGeneratorV2()

    print(f"\n{'='*60}")
    print(f"Generating SSP section for {control_id}")
    print(f"{'='*60}\n")

    result = gen.generate_section(control_id)

    parsed = result["parsed"]
    verification = result["verification"]

    print(f"Mode: {result['generation_mode']}")
    print(f"Evidence linked: {result['evidence_count']}")
    print(f"Status: {parsed['implementation_status']}")
    print(f"Verification: {verification.summary()}")

    if verification.findings:
        print(f"\nFindings:")
        for f in verification.findings:
            print(f"  [{f.severity}] {f.finding_type}: {f.value}")

    print(f"\nNarrative (first 500 chars):")
    print(parsed["narrative"][:500])

    if parsed.get("gaps"):
        print(f"\nGaps ({len(parsed['gaps'])}):")
        for gap in parsed["gaps"]:
            print(f"  - [{gap['gap_type']}] {gap['description']}")

    return result


# Backward-compat alias: old code imports SSPGenerator
SSPGenerator = SSPGeneratorV2


if __name__ == "__main__":
    import sys
    cid = sys.argv[1] if len(sys.argv) > 1 else "AC.L2-3.1.1"
    test_single_control(cid)
