"""
Chunking strategy for NIST 800-171 compliance content.

Three types of chunks for Qdrant:
1. Control chunks — one per control (110 total), includes description + discussion
2. Objective chunks — one per objective (246+), includes EIT data
3. Family overview chunks — one per family (14), aggregated context

Each chunk carries metadata for filtering and citation tracking.
"""

import sys
import os
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from data.nist.controls_full import NIST_800_171_CONTROLS
from data.nist.objectives_full import ASSESSMENT_OBJECTIVES


def chunk_controls() -> List[Dict[str, Any]]:
    """Create one chunk per NIST 800-171 control.

    Each chunk includes the control description, discussion, and metadata.
    This is the primary retrieval target for SSP generation.
    """
    chunks = []
    for ctrl in NIST_800_171_CONTROLS:
        text = (
            f"NIST 800-171 Control {ctrl['id']} ({ctrl['nist_id']}): "
            f"{ctrl['title']}\n\n"
            f"Family: {ctrl['family']}\n\n"
            f"Requirement: {ctrl['description']}\n\n"
            f"Discussion: {ctrl['discussion']}\n\n"
            f"SPRS Weight: {ctrl['points']} point(s)\n"
            f"POA&M Eligible: {ctrl['poam_eligible']}"
        )
        chunks.append({
            "id": f"control-{ctrl['id']}",
            "text": text,
            "metadata": {
                "type": "control",
                "control_id": ctrl["id"],
                "nist_id": ctrl["nist_id"],
                "family": ctrl["family"],
                "family_id": ctrl["family_id"],
                "title": ctrl["title"],
                "points": ctrl["points"],
                "poam_eligible": ctrl["poam_eligible"],
                "source": "NIST SP 800-171 Rev 2",
            }
        })
    return chunks


def chunk_objectives() -> List[Dict[str, Any]]:
    """Create one chunk per assessment objective.

    Each chunk includes the determination statement plus EIT methodology.
    This is the retrieval target for evidence mapping and gap assessment.
    """
    # Build a lookup for control titles
    ctrl_lookup = {c["id"]: c for c in NIST_800_171_CONTROLS}

    chunks = []
    for obj in ASSESSMENT_OBJECTIVES:
        ctrl = ctrl_lookup.get(obj["control_id"], {})
        text = (
            f"Assessment Objective {obj['id']} for Control "
            f"{obj['control_id']} ({ctrl.get('title', 'Unknown')})\n\n"
            f"Determination Statement: {obj['description']}\n\n"
            f"EXAMINE: {obj['examine']}\n\n"
            f"INTERVIEW: {obj['interview']}\n\n"
            f"TEST: {obj['test']}"
        )
        chunks.append({
            "id": f"objective-{obj['id']}",
            "text": text,
            "metadata": {
                "type": "objective",
                "objective_id": obj["id"],
                "control_id": obj["control_id"],
                "family": ctrl.get("family", "Unknown"),
                "family_id": ctrl.get("family_id", ""),
                "source": "NIST SP 800-171A",
            }
        })
    return chunks


def chunk_family_overviews() -> List[Dict[str, Any]]:
    """Create one overview chunk per control family.

    Aggregates all controls in a family into a single summary chunk.
    Useful for broad queries like "What does Access Control cover?"
    """
    from collections import defaultdict
    families = defaultdict(list)
    for ctrl in NIST_800_171_CONTROLS:
        families[ctrl["family"]].append(ctrl)

    chunks = []
    for family_name, controls in families.items():
        family_id = controls[0]["family_id"]
        total_points = sum(c["points"] for c in controls)

        control_list = "\n".join(
            f"  - {c['id']} ({c['nist_id']}): {c['title']} "
            f"[{c['points']}pt, POA&M: {c['poam_eligible']}]"
            for c in controls
        )

        text = (
            f"NIST 800-171 Family: {family_name} ({family_id})\n\n"
            f"Total controls: {len(controls)}\n"
            f"Total SPRS points at risk: {total_points}\n\n"
            f"Controls in this family:\n{control_list}\n\n"
            f"This family covers the following areas within "
            f"CMMC Level 2 compliance for protecting CUI."
        )
        chunks.append({
            "id": f"family-{family_id}",
            "text": text,
            "metadata": {
                "type": "family_overview",
                "family": family_name,
                "family_id": family_id,
                "control_count": len(controls),
                "total_points": total_points,
                "source": "NIST SP 800-171 Rev 2",
            }
        })
    return chunks


def get_all_chunks() -> List[Dict[str, Any]]:
    """Get all chunks for loading into Qdrant."""
    controls = chunk_controls()
    objectives = chunk_objectives()
    families = chunk_family_overviews()

    all_chunks = controls + objectives + families
    print(f"Total chunks generated:")
    print(f"  Controls:  {len(controls)}")
    print(f"  Objectives: {len(objectives)}")
    print(f"  Families:  {len(families)}")
    print(f"  TOTAL:     {len(all_chunks)}")
    return all_chunks


if __name__ == "__main__":
    chunks = get_all_chunks()
    # Show a sample
    print(f"\n--- Sample control chunk ---")
    print(chunks[0]["text"][:300])
    print(f"\n--- Sample objective chunk ---")
    ctrl_count = len([c for c in chunks if c["metadata"]["type"] == "control"])
    print(chunks[ctrl_count]["text"][:300])
