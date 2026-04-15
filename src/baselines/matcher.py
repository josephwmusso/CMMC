"""
src/baselines/matcher.py

Match scan findings against an org's adopted baselines to detect
deviations, plus a summary helper for the Overview page.

Matching is keyword + plugin-family based — the baseline item carries
``match_keywords`` (list[str]) and ``match_plugin_families`` (list[str]);
a finding matches if either the family appears in the finding's
plugin_family, or any keyword is a case-insensitive substring of the
finding's plugin_name/synopsis/description.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from sqlalchemy import text


def _generate_id(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()[:20]


def _finding_matches_item(
    finding,
    keywords: list | None,
    families: list | None,
    plugin_ids: list | None,
) -> bool:
    """Two-tier match.

    Tier 1 (exact): when the item carries ``match_plugin_ids``, we ONLY
    match findings whose plugin_id is in that list. Keywords are ignored
    — plugin IDs are authoritative when present and prevent the keyword
    cross-contamination that made the Win11 match produce ~475 deviations.

    Tier 2 (fallback): when no plugin IDs are defined (M365 items,
    anything Nessus can't reach), fall back to plugin-family + keyword
    substring matching.
    """
    if plugin_ids:
        finding_pid = str(finding.plugin_id) if finding.plugin_id else ""
        return finding_pid in plugin_ids

    if families and finding.plugin_family:
        family_lower = finding.plugin_family.lower()
        for fam in families:
            if fam and fam.lower() in family_lower:
                return True

    if keywords:
        searchable = " ".join([
            finding.plugin_name or "",
            finding.synopsis or "",
            finding.description or "",
        ]).lower()
        for kw in keywords:
            if kw and kw.lower() in searchable:
                return True

    return False


def _extract_actual_value(finding) -> str:
    parts = []
    if finding.plugin_name:
        parts.append(finding.plugin_name)
    if finding.synopsis:
        parts.append(finding.synopsis)
    return " — ".join(parts)[:500]


def match_scan_to_baselines(db, org_id: str, scan_import_id: str) -> dict:
    """Compare scan findings against every ACTIVE baseline the org has adopted.

    Creates baseline_deviations rows for new matches; skips rows that
    already exist for the same (org_baseline, item, finding) triple.
    Caller is NOT expected to commit — this function commits at the end.
    """
    org_baselines = db.execute(text("""
        SELECT id AS org_baseline_id, baseline_id
        FROM org_baselines
        WHERE org_id = :org_id AND status = 'ACTIVE'
    """), {"org_id": org_id}).fetchall()

    if not org_baselines:
        return {
            "deviations_created": 0,
            "deviations_skipped": 0,
            "items_checked":      0,
            "baselines_checked":  0,
        }

    findings = db.execute(text("""
        SELECT id, plugin_id, plugin_name, plugin_family, synopsis, description, severity
        FROM scan_findings
        WHERE scan_import_id = :scan_id
          AND severity >= 1
    """), {"scan_id": scan_import_id}).fetchall()

    if not findings:
        return {
            "deviations_created": 0,
            "deviations_skipped": 0,
            "items_checked":      0,
            "baselines_checked":  len(org_baselines),
        }

    total_created = 0
    total_skipped = 0
    total_items   = 0
    now = datetime.now(timezone.utc)

    for ob in org_baselines:
        items = db.execute(text("""
            SELECT id, title, severity,
                   match_keywords, match_plugin_families, match_plugin_ids
            FROM baseline_items
            WHERE baseline_id = :baseline_id
        """), {"baseline_id": ob.baseline_id}).fetchall()

        total_items += len(items)

        for item in items:
            keywords   = item.match_keywords or []
            families   = item.match_plugin_families or []
            plugin_ids = item.match_plugin_ids or []

            for finding in findings:
                if not _finding_matches_item(finding, keywords, families, plugin_ids):
                    continue

                existing = db.execute(text("""
                    SELECT 1 FROM baseline_deviations
                    WHERE org_baseline_id  = :ob_id
                      AND baseline_item_id = :item_id
                      AND scan_finding_id  = :finding_id
                """), {
                    "ob_id":      ob.org_baseline_id,
                    "item_id":    item.id,
                    "finding_id": finding.id,
                }).fetchone()

                if existing:
                    total_skipped += 1
                    continue

                dev_id = _generate_id(
                    f"dev:{ob.org_baseline_id}:{item.id}:{finding.id}"
                )
                db.execute(text("""
                    INSERT INTO baseline_deviations
                        (id, org_id, org_baseline_id, baseline_item_id,
                         scan_finding_id, actual_value, status, detected_at)
                    VALUES
                        (:id, :org_id, :ob_id, :item_id,
                         :finding_id, :actual_value, 'OPEN', :now)
                """), {
                    "id":           dev_id,
                    "org_id":       org_id,
                    "ob_id":        ob.org_baseline_id,
                    "item_id":      item.id,
                    "finding_id":   finding.id,
                    "actual_value": _extract_actual_value(finding),
                    "now":          now,
                })
                total_created += 1

    db.commit()

    return {
        "deviations_created": total_created,
        "deviations_skipped": total_skipped,
        "items_checked":      total_items,
        "baselines_checked":  len(org_baselines),
    }


def get_baseline_summary(db, org_id: str) -> dict:
    """Overview-page summary: adoption count, open/remediated deviations,
    compliance %, severity breakdown, top 5 affected NIST controls."""
    adopted = db.execute(text("""
        SELECT COUNT(*) FROM org_baselines
        WHERE org_id = :org_id AND status = 'ACTIVE'
    """), {"org_id": org_id}).scalar() or 0

    if adopted == 0:
        return {
            "baselines_adopted":      0,
            "total_items":            0,
            "open_deviations":        0,
            "remediated_deviations":  0,
            "compliance_pct":         0.0,
            "by_severity":            {},
            "top_controls_affected":  [],
        }

    total_items = db.execute(text("""
        SELECT COUNT(DISTINCT bi.id)
        FROM baseline_items bi
        JOIN org_baselines ob ON bi.baseline_id = ob.baseline_id
        WHERE ob.org_id = :org_id AND ob.status = 'ACTIVE'
    """), {"org_id": org_id}).scalar() or 0

    open_devs = db.execute(text("""
        SELECT COUNT(*) FROM baseline_deviations
        WHERE org_id = :org_id AND status = 'OPEN'
    """), {"org_id": org_id}).scalar() or 0

    remediated = db.execute(text("""
        SELECT COUNT(*) FROM baseline_deviations
        WHERE org_id = :org_id AND status = 'REMEDIATED'
    """), {"org_id": org_id}).scalar() or 0

    severity_rows = db.execute(text("""
        SELECT bi.severity, COUNT(*) AS cnt
        FROM baseline_deviations bd
        JOIN baseline_items bi ON bd.baseline_item_id = bi.id
        WHERE bd.org_id = :org_id AND bd.status = 'OPEN'
        GROUP BY bi.severity
    """), {"org_id": org_id}).fetchall()
    by_severity = {row.severity: row.cnt for row in severity_rows}

    control_rows = db.execute(text("""
        SELECT unnest(bi.control_ids) AS control_id,
               COUNT(DISTINCT bd.id)   AS cnt
        FROM baseline_deviations bd
        JOIN baseline_items bi ON bd.baseline_item_id = bi.id
        WHERE bd.org_id = :org_id AND bd.status = 'OPEN'
        GROUP BY control_id
        ORDER BY cnt DESC
        LIMIT 5
    """), {"org_id": org_id}).fetchall()
    top_controls = [{"control_id": r.control_id, "count": r.cnt} for r in control_rows]

    items_with_open = db.execute(text("""
        SELECT COUNT(DISTINCT bd.baseline_item_id)
        FROM baseline_deviations bd
        JOIN org_baselines ob ON bd.org_baseline_id = ob.id
        WHERE bd.org_id = :org_id
          AND bd.status = 'OPEN'
          AND ob.status = 'ACTIVE'
    """), {"org_id": org_id}).scalar() or 0

    compliance_pct = (
        ((total_items - items_with_open) / total_items) * 100.0
        if total_items > 0 else 0.0
    )

    return {
        "baselines_adopted":     adopted,
        "total_items":           total_items,
        "open_deviations":       open_devs,
        "remediated_deviations": remediated,
        "compliance_pct":        round(compliance_pct, 1),
        "by_severity":           by_severity,
        "top_controls_affected": top_controls,
    }
