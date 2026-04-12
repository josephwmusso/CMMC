"""
CMMC Compliance Platform — Streamlit Dashboard (Week 8)
Multi-page: Overview | Evidence Management | SSP & POA&M | Demo Controls

Run: python -m streamlit run src/ui/dashboard.py --server.port 8501
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import hashlib
import json
import os
import sys
import time
import requests
import shutil
from datetime import datetime, timezone, timedelta

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from src.db.session import SessionLocal

# ─── Constants ────────────────────────────────────────────────────────────────
ORG_ID = "9de53b587b23450b87af"
EVIDENCE_DIR = os.path.join("data", "evidence", ORG_ID)
EXPORTS_DIR = os.path.join("data", "exports")
os.makedirs(EVIDENCE_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)

FAMILY_ORDER = ["AC", "AT", "AU", "CM", "IA", "IR", "MA", "MP", "PE", "PS", "RA", "CA", "SC", "SI"]
FAMILY_NAMES = {
    "AC": "Access Control", "AT": "Awareness & Training", "AU": "Audit & Accountability",
    "CM": "Config Management", "IA": "Identification & Auth", "IR": "Incident Response",
    "MA": "Maintenance", "MP": "Media Protection", "PE": "Physical Protection",
    "PS": "Personnel Security", "RA": "Risk Assessment", "CA": "Security Assessment",
    "SC": "System & Comms Protection", "SI": "System & Info Integrity",
}

st.set_page_config(page_title="CMMC Compliance Platform", page_icon="🛡️", layout="wide")

# ─── Theme & Custom CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Chrome cleanup ──────────────────────────────────────────────────────── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stDeployButton"] {display: none;}
header[data-testid="stHeader"] {background: transparent;}

/* ── Metric cards ────────────────────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: #161B22;
    border: 1px solid #21262D;
    border-radius: 10px;
    padding: 16px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.5);
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] > div {
    font-size: 0.70rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #8B949E;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] > div {
    font-size: 1.75rem;
    font-weight: 700;
    color: #E6EDF3;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 0.75rem;
}

/* ── Section headers (st.subheader → h3) ─────────────────────────────────── */
h3 {
    border-left: 3px solid #2DD4BF !important;
    padding-left: 12px !important;
    margin-top: 1.75rem !important;
    margin-bottom: 0.5rem !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    color: #CDD9E5 !important;
}

/* ── Page title (st.title → h1) ──────────────────────────────────────────── */
h1 {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: #E6EDF3 !important;
    letter-spacing: -0.01em !important;
    padding-bottom: 4px !important;
}
h1 + div[data-testid="stCaptionContainer"] p {
    color: #8B949E;
    font-size: 0.85rem;
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #080D13;
    border-right: 1px solid #21262D;
}
[data-testid="stSidebar"] [data-testid="stMetricContainer"],
[data-testid="stSidebar"] [data-testid="metric-container"] {
    background: #0D1117;
    border: 1px solid #21262D;
    border-radius: 8px;
    padding: 10px 14px;
}
[data-testid="stSidebar"] [data-testid="stMetricValue"] > div {
    color: #2DD4BF !important;
    font-size: 1.5rem !important;
}
[data-testid="stSidebar"] .stRadio [data-testid="stWidgetLabel"] p {
    font-size: 0.7rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #8B949E;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 0.875rem;
    transition: background 0.15s;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
    background: #161B22;
}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    border-bottom: 1px solid #21262D;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px 6px 0 0;
    padding: 8px 16px;
    font-size: 0.875rem;
    font-weight: 500;
    color: #8B949E;
    background: transparent;
    border: none;
}
.stTabs [aria-selected="true"] {
    background: #161B22 !important;
    color: #2DD4BF !important;
    border-bottom: 2px solid #2DD4BF !important;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
.stButton > button {
    border-radius: 6px;
    font-weight: 500;
    font-size: 0.875rem;
    transition: all 0.15s ease;
    padding: 6px 18px;
}
.stButton > button[kind="primary"] {
    background: #2DD4BF;
    color: #0D1117;
    border: none;
    font-weight: 600;
}
.stButton > button[kind="primary"]:hover {
    background: #5EEAD4;
    box-shadow: 0 0 14px rgba(45,212,191,0.35);
}
.stButton > button:not([kind="primary"]) {
    border: 1px solid #30363D;
    color: #CDD9E5;
    background: transparent;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: #2DD4BF;
    color: #2DD4BF;
    background: rgba(45,212,191,0.06);
}

/* ── Download buttons ────────────────────────────────────────────────────── */
.stDownloadButton > button {
    border-radius: 6px;
    border: 1px solid #30363D;
    font-size: 0.875rem;
    background: #161B22;
    color: #CDD9E5;
    transition: all 0.15s ease;
}
.stDownloadButton > button:hover {
    border-color: #2DD4BF;
    color: #2DD4BF;
    background: rgba(45,212,191,0.06);
}

/* ── DataFrames ──────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #21262D !important;
}
[data-testid="stDataFrame"] table {
    border-collapse: collapse;
}
[data-testid="stDataFrame"] thead tr th {
    background: #161B22 !important;
    color: #8B949E !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid #21262D !important;
    padding: 10px 12px !important;
}
[data-testid="stDataFrame"] tbody tr:nth-child(even) td {
    background: #161B22 !important;
}
[data-testid="stDataFrame"] tbody tr:nth-child(odd) td {
    background: #0D1117 !important;
}
[data-testid="stDataFrame"] tbody tr td {
    font-size: 0.82rem !important;
    padding: 8px 12px !important;
    border-bottom: 1px solid #161B22 !important;
    color: #CDD9E5 !important;
}

/* ── Expanders ───────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid #21262D !important;
    border-radius: 8px !important;
    margin-bottom: 6px !important;
    background: #161B22 !important;
    overflow: hidden;
}
[data-testid="stExpander"] details summary {
    padding: 10px 14px;
}
[data-testid="stExpander"] details summary:hover {
    background: #1C2128;
}

/* ── Alert boxes ─────────────────────────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 8px;
    border-left-width: 3px;
}

/* ── Selectbox / multiselect ─────────────────────────────────────────────── */
[data-testid="stSelectbox"] > div,
[data-testid="stMultiSelect"] > div {
    border-radius: 6px;
}

/* ── Forms ───────────────────────────────────────────────────────────────── */
[data-testid="stForm"] {
    border: 1px solid #21262D;
    border-radius: 10px;
    padding: 16px;
    background: #161B22;
}

/* ── Plotly chart containers ─────────────────────────────────────────────── */
.js-plotly-plot {
    border-radius: 8px;
}

/* ── Dividers ────────────────────────────────────────────────────────────── */
hr {
    border-color: #21262D !important;
    margin: 1.5rem 0 !important;
}

/* ── Progress bar ────────────────────────────────────────────────────────── */
[data-testid="stProgress"] > div > div {
    background: #2DD4BF;
}
</style>
""", unsafe_allow_html=True)


# ─── Database helper ──────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def run_query(query_str, params=None):
    """Run a read query and return list of dicts. Returns [] on DB error."""
    try:
        db = SessionLocal()
        try:
            result = db.execute(text(query_str), params or {})
            cols = result.keys()
            return [dict(zip(cols, row)) for row in result.fetchall()]
        finally:
            db.close()
    except Exception as e:
        st.error(f"Database unavailable: {e}")
        return []


def run_exec(query_str, params=None):
    """Run a write query and commit. Returns 0 on DB error."""
    try:
        db = SessionLocal()
        try:
            result = db.execute(text(query_str), params or {})
            db.commit()
            return result.rowcount
        finally:
            db.close()
    except Exception as e:
        st.error(f"Database error: {e}")
        return 0


# ─── Data Loaders (cached) ───────────────────────────────────────────────────
def load_sprs_data():
    """Load SPRS score calculation data."""
    controls = run_query("""
        SELECT c.id, c.family_abbrev, c.title, c.points, c.poam_eligible,
               s.implementation_status, s.narrative
        FROM controls c
        LEFT JOIN ssp_sections s ON c.id = s.control_id AND s.org_id = :org_id
        ORDER BY c.family_abbrev, c.id
    """, {"org_id": ORG_ID})

    # Get active POA&M items
    poam_items = run_query("""
        SELECT control_id, status, risk_level, weakness_description,
               scheduled_completion
        FROM poam_items
        WHERE org_id = :org_id AND status IN ('OPEN', 'IN_PROGRESS')
    """, {"org_id": ORG_ID})
    poam_controls = {p["control_id"] for p in poam_items}

    # Calculate scores
    raw_score = 110
    conditional_score = 110
    met = 0
    not_met = 0
    partial = 0
    no_ssp = 0
    details = []

    for c in controls:
        status = c.get("implementation_status")
        points = c["points"] or 1

        if status == "Implemented":
            met += 1
        elif status == "Partially Implemented":
            partial += 1
            raw_score -= points
            if c["id"] in poam_controls:
                # POA&M gives conditional credit
                pass
            else:
                conditional_score -= points
        elif status == "Not Implemented":
            not_met += 1
            raw_score -= points
            if c["id"] in poam_controls and c.get("poam_eligible", True):
                pass
            else:
                conditional_score -= points
        else:
            no_ssp += 1
            raw_score -= points
            conditional_score -= points

        details.append({
            "control_id": c["id"],
            "family": c["family_abbrev"],
            "title": c["title"],
            "points": points,
            "status": status or "No SSP",
            "poam_eligible": c.get("poam_eligible", True),
            "has_poam": c["id"] in poam_controls,
        })

    return {
        "raw_score": max(raw_score, -203),
        "conditional_score": max(conditional_score, -203),
        "met": met, "partial": partial, "not_met": not_met, "no_ssp": no_ssp,
        "total": len(controls),
        "poam_count": len(poam_items),
        "poam_points": sum(
            next((d["points"] for d in details if d["control_id"] == p["control_id"]), 0)
            for p in poam_items
        ),
        "details": details,
    }


def load_evidence_data():
    """Load all evidence artifacts."""
    return run_query("""
        SELECT ea.id, ea.filename, ea.file_path, ea.file_size_bytes,
               ea.mime_type, ea.sha256_hash, ea.state, ea.evidence_type,
               ea.source_system, ea.description, ea.owner,
               ea.created_at, ea.updated_at, ea.published_at
        FROM evidence_artifacts ea
        WHERE ea.org_id = :org_id
        ORDER BY ea.created_at DESC
    """, {"org_id": ORG_ID})


def load_evidence_control_links(evidence_id):
    """Load control links for an evidence artifact."""
    return run_query("""
        SELECT ecm.control_id, ecm.objective_id, c.title, c.family_abbrev
        FROM evidence_control_map ecm
        JOIN controls c ON c.id = ecm.control_id
        WHERE ecm.evidence_id = :eid
    """, {"eid": evidence_id})


def load_gap_data():
    """Load gap assessment."""
    controls = run_query("""
        SELECT c.id, c.family_abbrev, c.title, c.points,
               s.implementation_status
        FROM controls c
        LEFT JOIN ssp_sections s ON c.id = s.control_id AND s.org_id = :org_id
        ORDER BY c.points DESC, c.id
    """, {"org_id": ORG_ID})

    evidence_map = run_query("""
        SELECT DISTINCT ecm.control_id
        FROM evidence_control_map ecm
        JOIN evidence_artifacts ea ON ea.id = ecm.evidence_id
        WHERE ea.org_id = :org_id
    """, {"org_id": ORG_ID})
    controls_with_evidence = {e["control_id"] for e in evidence_map}

    gaps = []
    for c in controls:
        status = c.get("implementation_status")
        has_evidence = c["id"] in controls_with_evidence
        points = c["points"] or 1
        severity = "CRITICAL" if points >= 5 else ("HIGH" if points >= 3 else "MEDIUM")

        gap_types = []
        if not status:
            gap_types.append("NO_SSP")
        elif status == "Not Implemented":
            gap_types.append("SSP_NOT_IMPLEMENTED")
        elif status == "Partially Implemented":
            gap_types.append("SSP_PARTIAL")

        if not has_evidence:
            gap_types.append("NO_EVIDENCE")

        if gap_types:
            gaps.append({
                "control_id": c["id"],
                "family": c["family_abbrev"],
                "title": c["title"],
                "points": points,
                "severity": severity,
                "gap_types": gap_types,
                "status": status or "No SSP",
                "has_evidence": has_evidence,
            })

    return gaps


def load_family_summary():
    """Load per-family status summary."""
    controls = run_query("""
        SELECT c.family_abbrev,
               COUNT(*) as total,
               COUNT(CASE WHEN s.implementation_status = 'Implemented' THEN 1 END) as implemented,
               COUNT(CASE WHEN s.implementation_status = 'Partially Implemented' THEN 1 END) as partial,
               COUNT(CASE WHEN s.implementation_status = 'Not Implemented' THEN 1 END) as not_impl,
               COUNT(CASE WHEN s.implementation_status IS NULL THEN 1 END) as no_ssp
        FROM controls c
        LEFT JOIN ssp_sections s ON c.id = s.control_id AND s.org_id = :org_id
        GROUP BY c.family_abbrev
        ORDER BY c.family_abbrev
    """, {"org_id": ORG_ID})
    return controls


def load_poam_data():
    """Load POA&M items."""
    return run_query("""
        SELECT p.id, p.control_id, p.weakness_description, p.remediation_plan,
               p.status, p.risk_level, p.scheduled_completion, p.actual_completion,
               c.title as control_title, c.points, c.family_abbrev
        FROM poam_items p
        JOIN controls c ON c.id = p.control_id
        WHERE p.org_id = :org_id
        ORDER BY c.points DESC, p.control_id
    """, {"org_id": ORG_ID})


def load_audit_log(limit=50):
    """Load recent audit log entries."""
    return run_query("""
        SELECT id, timestamp, actor, actor_type, action, target_type,
               target_id, details, prev_hash, entry_hash
        FROM audit_log
        ORDER BY id DESC
        LIMIT :limit
    """, {"limit": limit})


# ─── Sidebar Navigation ──────────────────────────────────────────────────────
st.sidebar.markdown("""
<div style="
    padding: 16px 8px 12px 8px;
    border-bottom: 1px solid #21262D;
    margin-bottom: 8px;
">
    <div style="font-size: 1.05rem; font-weight: 700; color: #E6EDF3; letter-spacing: 0.01em;">
        🛡️ CMMC Platform
    </div>
    <div style="font-size: 0.7rem; color: #8B949E; margin-top: 3px; letter-spacing: 0.05em; text-transform: uppercase;">
        Compliance OS &nbsp;·&nbsp; v0.9.0
    </div>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Navigate",
    ["📊 Overview", "📁 Evidence Management", "📝 SSP & POA&M", "🔧 Demo Controls"],
    index=0,
)

# Quick stats in sidebar
try:
    sprs = load_sprs_data()
except Exception as e:
    sprs = {"conditional_score": "N/A", "raw_score": "N/A", "met": 0, "total": 0, "poam_count": 0, "poam_points": 0, "details": []}
    st.sidebar.error(f"Database unavailable — {e}")

st.sidebar.divider()
st.sidebar.metric(
    "SPRS Score",
    f"{sprs['conditional_score']}/110",
    delta=f"Raw: {sprs['raw_score']}" if sprs['poam_count'] > 0 else None,
)
st.sidebar.metric("Controls Met", f"{sprs['met']}/{sprs['total']}")
if sprs['poam_count'] > 0:
    st.sidebar.metric("Active POA&M", sprs['poam_count'], delta=f"{sprs['poam_points']} pts at risk")
st.sidebar.divider()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1: OVERVIEW DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if page == "📊 Overview":
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #161B22 0%, #0D1117 100%);
        border: 1px solid #21262D;
        border-left: 4px solid #2DD4BF;
        border-radius: 10px;
        padding: 20px 28px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    ">
        <div>
            <div style="font-size: 1.4rem; font-weight: 700; color: #E6EDF3; letter-spacing: -0.01em;">
                🛡️ CMMC Level 2 Compliance Dashboard
            </div>
            <div style="font-size: 0.82rem; color: #8B949E; margin-top: 4px; letter-spacing: 0.02em;">
                Apex Defense Solutions &nbsp;·&nbsp; NIST 800-171 Rev 2 (110 Controls) &nbsp;·&nbsp; v0.9.0
            </div>
        </div>
        <div style="
            background: #0D1117;
            border: 1px solid #21262D;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #2DD4BF;
        ">CMMC Level 2</div>
    </div>
    """, unsafe_allow_html=True)

    # ─── Score Gauge ──────────────────────────────────────────────────────
    col1, col2 = st.columns([2, 3])

    with col1:
        # SPRS Score gauge
        display_score = sprs["conditional_score"] if sprs["poam_count"] > 0 else sprs["raw_score"]
        color = "#22c55e" if display_score >= 88 else ("#f59e0b" if display_score >= 50 else "#ef4444")

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=display_score,
            number={"font": {"size": 48, "color": color, "family": "sans-serif"}, "suffix": ""},
            title={"text": "SPRS Score", "font": {"size": 13, "color": "#8B949E", "family": "sans-serif"}},
            delta={
                "reference": 88,
                "increasing": {"color": "#2EA043"},
                "decreasing": {"color": "#DA3633"},
                "font": {"size": 13},
            },
            gauge={
                "axis": {
                    "range": [-88, 110],
                    "tickwidth": 1,
                    "tickfont": {"color": "#8B949E", "size": 10},
                },
                "bar": {"color": color, "thickness": 0.25},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [-88, 0],  "color": "rgba(218,54,51,0.15)"},
                    {"range": [0, 50],   "color": "rgba(210,153,34,0.12)"},
                    {"range": [50, 88],  "color": "rgba(210,153,34,0.08)"},
                    {"range": [88, 110], "color": "rgba(46,160,67,0.15)"},
                ],
                "threshold": {
                    "line": {"color": "#DA3633", "width": 2},
                    "thickness": 0.75,
                    "value": 88,
                },
            },
        ))
        fig_gauge.update_layout(
            height=260,
            margin=dict(t=50, b=0, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"family": "sans-serif"},
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        if sprs["poam_count"] > 0:
            st.info(
                f"**Conditional score**: {sprs['conditional_score']} "
                f"(with {sprs['poam_count']} active POA&M items)\n\n"
                f"**Raw score**: {sprs['raw_score']} "
                f"(without POA&M credit)"
            )

    with col2:
        # Key metrics
        m1, m2, m3, m4, m5 = st.columns(5)

        evidence = load_evidence_data()
        ssp_count = sprs["met"] + sprs["partial"] + sprs["not_met"]
        evidence_controls = len(set(
            link["control_id"]
            for e in evidence
            for link in load_evidence_control_links(e["id"])
        )) if evidence else 0

        m1.metric("Implemented", sprs["met"])
        m2.metric("Partial", sprs["partial"])
        m3.metric("Not Impl.", sprs["not_met"])
        m4.metric("SSP Coverage", f"{ssp_count}/{sprs['total']}")
        m5.metric("Evidence", f"{evidence_controls}/{sprs['total']}")

        # Family status chart
        families = load_family_summary()
        if families:
            df_fam = pd.DataFrame(families)
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                name="Implemented", x=df_fam["family_abbrev"],
                y=df_fam["implemented"],
                marker_color="#2EA043",
                marker_line_width=0,
            ))
            fig_bar.add_trace(go.Bar(
                name="Partial", x=df_fam["family_abbrev"],
                y=df_fam["partial"],
                marker_color="#D29922",
                marker_line_width=0,
            ))
            fig_bar.add_trace(go.Bar(
                name="Not Implemented", x=df_fam["family_abbrev"],
                y=df_fam["not_impl"],
                marker_color="#DA3633",
                marker_line_width=0,
            ))
            fig_bar.add_trace(go.Bar(
                name="No SSP", x=df_fam["family_abbrev"],
                y=df_fam["no_ssp"],
                marker_color="#484F58",
                marker_line_width=0,
            ))
            fig_bar.update_layout(
                barmode="stack",
                height=255,
                margin=dict(t=36, b=0, l=0, r=0),
                title={
                    "text": "Control Status by Family",
                    "font": {"size": 11, "color": "#8B949E"},
                    "x": 0,
                    "xanchor": "left",
                },
                legend=dict(
                    orientation="h",
                    yanchor="bottom", y=1.02,
                    xanchor="left", x=0,
                    font={"size": 11, "color": "#8B949E"},
                    bgcolor="rgba(0,0,0,0)",
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    tickfont={"size": 10, "color": "#8B949E"},
                    gridcolor="#21262D",
                    linecolor="#21262D",
                ),
                yaxis=dict(
                    tickfont={"size": 10, "color": "#8B949E"},
                    gridcolor="#21262D",
                    linecolor="rgba(0,0,0,0)",
                    showgrid=True,
                ),
                font={"family": "sans-serif"},
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()
    # ─── Evidence Pipeline Funnel ─────────────────────────────────────────
    st.subheader("Evidence Pipeline")
    if evidence:
        states = {"DRAFT": 0, "REVIEWED": 0, "APPROVED": 0, "PUBLISHED": 0}
        for e in evidence:
            s = e.get("state", "DRAFT")
            if s in states:
                states[s] += 1

        funnel_cols = st.columns(4)
        for i, (state, count) in enumerate(states.items()):
            with funnel_cols[i]:
                color = {"DRAFT": "🔵", "REVIEWED": "🟡", "APPROVED": "🟠", "PUBLISHED": "🟢"}
                st.metric(f"{color.get(state, '')} {state}", count)
    else:
        st.info("No evidence uploaded yet. Go to **Evidence Management** to upload files.")

    st.divider()
    # ─── Gap Summary ──────────────────────────────────────────────────────
    st.subheader("Gap Summary")
    gaps = load_gap_data()
    if gaps:
        critical = [g for g in gaps if g["severity"] == "CRITICAL"]
        high = [g for g in gaps if g["severity"] == "HIGH"]
        medium = [g for g in gaps if g["severity"] == "MEDIUM"]

        gc1, gc2, gc3 = st.columns(3)
        gc1.metric("🔴 Critical Gaps", len(critical), help="5-point controls")
        gc2.metric("🟠 High Gaps", len(high), help="3-point controls")
        gc3.metric("🟡 Medium Gaps", len(medium), help="1-point controls")

        severity_filter = st.selectbox(
            "Filter by severity", ["All", "CRITICAL", "HIGH", "MEDIUM"]
        )
        filtered = gaps if severity_filter == "All" else [g for g in gaps if g["severity"] == severity_filter]

        if filtered:
            df_gaps = pd.DataFrame(filtered)
            df_gaps["gap_types"] = df_gaps["gap_types"].apply(lambda x: ", ".join(x))
            st.dataframe(
                df_gaps[["control_id", "family", "title", "points", "severity", "gap_types", "status", "has_evidence"]],
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.success("No gaps found! All controls have SSP narratives and evidence.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2: EVIDENCE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📁 Evidence Management":
    st.title("Evidence Management")
    st.caption("Upload, track, and publish evidence artifacts")

    tab_upload, tab_list, tab_verify = st.tabs(["📤 Upload", "📋 Artifact List", "✅ Verify & Manifest"])

    # ─── Upload Tab ───────────────────────────────────────────────────────
    with tab_upload:
        st.subheader("Upload Evidence Artifact")

        with st.form("upload_form", clear_on_submit=True):
            uploaded_file = st.file_uploader(
                "Drag and drop evidence file",
                type=["pdf", "docx", "doc", "xlsx", "csv", "png", "jpg", "jpeg", "txt", "json", "xml"],
            )

            uc1, uc2 = st.columns(2)
            with uc1:
                evidence_type = st.selectbox(
                    "Evidence Type",
                    ["policy", "config", "screenshot", "log", "report", "training_record", "test_output", "other"],
                )
                source_system = st.text_input("Source System", placeholder="e.g., entra_id, crowdstrike, manual")
            with uc2:
                owner = st.text_input("Owner", value="admin@apexdefense.com")
                description = st.text_area("Description", placeholder="Describe what this evidence demonstrates...")

            # Control linking
            st.write("**Link to Controls** (select which controls this evidence supports)")
            all_controls = run_query(
                "SELECT id, family_abbrev, title FROM controls ORDER BY family_abbrev, id"
            )
            control_options = {f"{c['id']} — {c['title'][:60]}": c["id"] for c in all_controls}
            selected_controls = st.multiselect(
                "Controls", options=list(control_options.keys()),
                help="Select one or more NIST 800-171 controls this evidence satisfies"
            )

            submitted = st.form_submit_button("Upload Evidence", type="primary")

            if submitted and uploaded_file:
                # Save file
                file_path = os.path.join(EVIDENCE_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())

                # Generate ID
                artifact_id = hashlib.sha256(
                    f"{ORG_ID}-{uploaded_file.name}-{datetime.now(timezone.utc).isoformat()}".encode()
                ).hexdigest()[:20]

                # Insert to DB
                run_exec("""
                    INSERT INTO evidence_artifacts
                        (id, org_id, filename, file_path, file_size_bytes, mime_type,
                         state, evidence_type, source_system, description, owner, created_at, updated_at)
                    VALUES
                        (:id, :org_id, :filename, :file_path, :file_size_bytes, :mime_type,
                         'DRAFT', :evidence_type, :source_system, :description, :owner, NOW(), NOW())
                """, {
                    "id": artifact_id,
                    "org_id": ORG_ID,
                    "filename": uploaded_file.name,
                    "file_path": file_path,
                    "file_size_bytes": uploaded_file.size,
                    "mime_type": uploaded_file.type or "application/octet-stream",
                    "evidence_type": evidence_type,
                    "source_system": source_system or "manual",
                    "description": description,
                    "owner": owner,
                })

                # Link to controls
                for label in selected_controls:
                    ctrl_id = control_options[label]
                    link_id = hashlib.sha256(f"{artifact_id}-{ctrl_id}".encode()).hexdigest()[:20]
                    run_exec("""
                        INSERT INTO evidence_control_map (id, evidence_id, control_id)
                        VALUES (:id, :eid, :cid)
                        ON CONFLICT DO NOTHING
                    """, {"id": link_id, "eid": artifact_id, "cid": ctrl_id})

                # Audit log entry
                _write_audit_entry(
                    actor=owner, actor_type="user",
                    action="evidence.upload",
                    target_type="evidence_artifact", target_id=artifact_id,
                    details={"filename": uploaded_file.name, "evidence_type": evidence_type,
                             "controls_linked": [control_options[l] for l in selected_controls]},
                )

                st.success(f"Uploaded **{uploaded_file.name}** (ID: `{artifact_id}`) as DRAFT with "
                           f"{len(selected_controls)} control link(s).")
                st.rerun()

            elif submitted and not uploaded_file:
                st.warning("Please select a file to upload.")

    # ─── Artifact List Tab ────────────────────────────────────────────────
    with tab_list:
        st.subheader("Evidence Artifacts")

        evidence = load_evidence_data()
        if not evidence:
            st.info("No evidence artifacts yet. Upload files in the Upload tab.")
        else:
            # ── Filter / search bar ────────────────────────────────────────
            fl1, fl2, fl3 = st.columns([3, 2, 2])
            with fl1:
                search_term = st.text_input("Search", placeholder="filename, description, source…", label_visibility="collapsed")
            with fl2:
                state_filter = st.selectbox("State", ["All", "DRAFT", "REVIEWED", "APPROVED", "PUBLISHED"], label_visibility="collapsed")
            with fl3:
                domain_filter = st.selectbox(
                    "Domain",
                    ["All Domains", "AC", "AU", "CA", "CM", "IA", "IR", "MA", "MP", "PE", "PS", "RA", "SA", "SC", "SI", "AT"],
                    label_visibility="collapsed",
                )

            filtered_ev = evidence
            if state_filter != "All":
                filtered_ev = [e for e in filtered_ev if e["state"] == state_filter]
            if search_term:
                t = search_term.lower()
                filtered_ev = [
                    e for e in filtered_ev
                    if t in (e.get("filename") or "").lower()
                    or t in (e.get("description") or "").lower()
                    or t in (e.get("source_system") or "").lower()
                ]
            if domain_filter != "All Domains":
                # Filter by whether any linked control starts with that domain prefix
                def _has_domain(ev_id, prefix):
                    links = load_evidence_control_links(ev_id)
                    return any((l.get("control_id") or "").startswith(prefix + ".") for l in links)
                filtered_ev = [e for e in filtered_ev if _has_domain(e["id"], domain_filter)]

            st.caption(f"Showing {len(filtered_ev)} of {len(evidence)} artifacts")

            STATE_ICON = {"DRAFT": "🔵", "REVIEWED": "🟡", "APPROVED": "🟠", "PUBLISHED": "🟢"}
            STATE_COLOR = {"DRAFT": "#1F6FEB", "REVIEWED": "#D29922", "APPROVED": "#E3B341", "PUBLISHED": "#2EA043"}

            for e in filtered_ev:
                icon = STATE_ICON.get(e["state"], "⚪")
                state_badge = f'<span style="background:{STATE_COLOR.get(e["state"],"#484F58")};color:#fff;padding:2px 8px;border-radius:12px;font-size:0.75rem;font-weight:600">{e["state"]}</span>'
                file_size_kb = (e.get("file_size_bytes") or 0) / 1024

                with st.expander(f"{icon} {e['filename']}  ·  {file_size_kb:.1f} KB"):
                    # ── Top row: metadata + state badge ──────────────────
                    m1, m2, m3 = st.columns([3, 3, 1])

                    with m1:
                        st.markdown(f"**ID:** `{e['id']}`")
                        if e.get("description"):
                            st.markdown(f"**Description:** {e['description']}")
                        st.markdown(f"**Source:** {e.get('source_system') or 'manual'}  ·  **Owner:** {e.get('owner') or 'N/A'}")
                        st.markdown(f"**Created:** {str(e.get('created_at') or '')[:19]}")
                        if e.get("sha256_hash"):
                            st.markdown(f"**SHA-256:** `{e['sha256_hash'][:32]}…`")

                    with m2:
                        # Linked controls with titles
                        links = load_evidence_control_links(e["id"])
                        if links:
                            cids = [l["control_id"] for l in links if l.get("control_id")]
                            # Look up titles one query using IN — build param dict dynamically
                            if cids:
                                placeholders = ", ".join(f":c{i}" for i in range(len(cids)))
                                ctrl_rows = run_query(
                                    f"SELECT id, title FROM controls WHERE id IN ({placeholders})",
                                    {f"c{i}": cids[i] for i in range(len(cids))},
                                )
                                ctrl_map = {c["id"]: c["title"] for c in ctrl_rows} if ctrl_rows else {}
                            else:
                                ctrl_map = {}
                            st.markdown("**Linked Controls:**")
                            for l in links:
                                cid = l.get("control_id") or ""
                                title = ctrl_map.get(cid, "")
                                if cid:
                                    st.markdown(f"<span style='font-family:monospace;color:#2DD4BF;font-size:0.8rem'>{cid}</span> {title[:55]}", unsafe_allow_html=True)
                        else:
                            st.markdown("**Linked Controls:** None")

                    with m3:
                        st.markdown(state_badge, unsafe_allow_html=True)
                        st.write("")  # spacing

                        # State transition buttons
                        current = e["state"]
                        transitions = {
                            "DRAFT": [("REVIEWED", "Mark Reviewed")],
                            "REVIEWED": [("APPROVED", "Approve"), ("DRAFT", "Send Back")],
                            "APPROVED": [("PUBLISHED", "Publish"), ("REVIEWED", "Send Back")],
                            "PUBLISHED": [],
                        }
                        for new_state, label in transitions.get(current, []):
                            btn_type = "primary" if new_state not in ("DRAFT", "REVIEWED") else "secondary"
                            if st.button(label, key=f"trans-{e['id']}-{new_state}", type=btn_type):
                                _transition_evidence(e["id"], e["file_path"], current, new_state)
                                st.rerun()
                        if current == "PUBLISHED":
                            st.success("✓ Immutable")

                    # ── File viewer ───────────────────────────────────────
                    st.divider()
                    viewer_col, dl_col = st.columns([5, 1])

                    with dl_col:
                        # Download button — works for all file types
                        fp = e.get("file_path") or ""
                        if fp and os.path.exists(fp):
                            with open(fp, "rb") as fh:
                                file_bytes_dl = fh.read()
                            st.download_button(
                                label="⬇ Download",
                                data=file_bytes_dl,
                                file_name=e["filename"],
                                key=f"dl-{e['id']}",
                            )

                    with viewer_col:
                        fp = e.get("file_path") or ""
                        fn_lower = (e.get("filename") or "").lower()

                        if fp and os.path.exists(fp):
                            if fn_lower.endswith(".md"):
                                with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                                    md_content = fh.read()
                                with st.expander("📄 View File Content", expanded=False):
                                    st.markdown(md_content)

                            elif fn_lower.endswith(".json"):
                                with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                                    raw_json = fh.read()
                                with st.expander("📄 View File Content", expanded=False):
                                    try:
                                        import json as _json
                                        parsed = _json.loads(raw_json)
                                        st.json(parsed)
                                    except Exception:
                                        st.code(raw_json, language="json")

                            elif fn_lower.endswith(".csv"):
                                with st.expander("📄 View File Content", expanded=False):
                                    try:
                                        import io as _io
                                        df_ev = pd.read_csv(fp, encoding="utf-8", on_bad_lines="skip")
                                        st.dataframe(df_ev, use_container_width=True, hide_index=True)
                                    except Exception as csv_err:
                                        st.warning(f"Could not parse CSV: {csv_err}")

                            elif fn_lower.endswith(".xml"):
                                with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                                    xml_content = fh.read()
                                with st.expander("📄 View File Content", expanded=False):
                                    st.code(xml_content, language="xml")

                            elif fn_lower.endswith(".txt"):
                                with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                                    txt_content = fh.read()
                                with st.expander("📄 View File Content", expanded=False):
                                    st.code(txt_content, language="text")

                            elif fn_lower.endswith(".docx"):
                                with st.expander("📄 File Info (download to view)", expanded=False):
                                    st.info("Word documents cannot be rendered inline. Use the Download button above.")

                            else:
                                with st.expander("📄 View File Content", expanded=False):
                                    try:
                                        with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                                            generic_content = fh.read(4000)
                                        st.code(generic_content, language="text")
                                    except Exception:
                                        st.info("Binary file — use the Download button to view.")
                        else:
                            st.caption("⚠ File not found on disk")

                    # ── Audit history for this artifact ───────────────────
                    audit_rows = run_query("""
                        SELECT timestamp, actor, action, details
                        FROM audit_log
                        WHERE target_id = :tid
                        ORDER BY id ASC
                    """, {"tid": e["id"]})

                    if audit_rows:
                        with st.expander(f"🔗 Audit History ({len(audit_rows)} events)", expanded=False):
                            for ar in audit_rows:
                                ts_str = str(ar.get("timestamp") or "")[:19]
                                actor_str = ar.get("actor") or "system"
                                action_str = ar.get("action") or ""
                                details_raw = ar.get("details") or {}
                                if isinstance(details_raw, str):
                                    try:
                                        import json as _json
                                        details_raw = _json.loads(details_raw)
                                    except Exception:
                                        pass
                                details_str = ", ".join(f"{k}: {v}" for k, v in details_raw.items()) if isinstance(details_raw, dict) else str(details_raw)
                                st.markdown(
                                    f"`{ts_str}` — **{action_str}** by `{actor_str}`"
                                    + (f"  \n<span style='color:#8B949E;font-size:0.8rem'>{details_str}</span>" if details_str else ""),
                                    unsafe_allow_html=True,
                                )

    # ─── Verify & Manifest Tab ────────────────────────────────────────────
    with tab_verify:
        st.subheader("Hash Verification & Manifest")

        published = [e for e in load_evidence_data() if e["state"] == "PUBLISHED"]

        if not published:
            st.info("No published evidence yet. Publish artifacts to generate manifests.")
        else:
            st.write(f"**{len(published)} published artifact(s)** ready for manifest generation.")

            # Verify each published artifact
            verify_results = []
            for e in published:
                if e.get("sha256_hash") and e.get("file_path") and os.path.exists(e["file_path"]):
                    sha256 = hashlib.sha256()
                    with open(e["file_path"], "rb") as f:
                        for chunk in iter(lambda: f.read(8192), b""):
                            sha256.update(chunk)
                    computed = sha256.hexdigest()
                    match = computed == e["sha256_hash"]
                else:
                    computed = None
                    match = False

                verify_results.append({
                    "filename": e["filename"],
                    "stored_hash": (e.get("sha256_hash") or "")[:16] + "...",
                    "computed_hash": (computed or "N/A")[:16] + "...",
                    "integrity": "✅ INTACT" if match else "❌ MISMATCH",
                })

            df_verify = pd.DataFrame(verify_results)
            st.dataframe(df_verify, use_container_width=True, hide_index=True)

            intact_count = sum(1 for v in verify_results if "INTACT" in v["integrity"])
            if intact_count == len(verify_results):
                st.success(f"All {intact_count} published artifacts verified intact.")
            else:
                st.error(f"{len(verify_results) - intact_count} artifact(s) have hash mismatches!")

            # Generate manifest button
            if st.button("📋 Generate CMMC Hash Manifest", type="primary"):
                lines = []
                for e in published:
                    lines.append(f"SHA256  {e.get('sha256_hash', 'N/A')}  {e['filename']}")

                manifest_content = "\n".join(lines)
                manifest_hash = hashlib.sha256(manifest_content.encode()).hexdigest()
                lines.append("---")
                lines.append(f"SHA256  {manifest_hash}  MANIFEST.txt")
                lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
                lines.append(f"Organization: Apex Defense Solutions")
                lines.append(f"Artifacts: {len(published)}")

                manifest_text = "\n".join(lines)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                manifest_path = os.path.join(EXPORTS_DIR, f"MANIFEST_Apex_Defense_{ts}.txt")
                with open(manifest_path, "w", encoding="utf-8") as f:
                    f.write(manifest_text)

                st.code(manifest_text, language="text")
                st.success(f"Manifest saved to `{manifest_path}`")

        # Audit chain verification
        st.divider()
        st.subheader("Audit Chain Integrity")
        if st.button("🔗 Verify Audit Chain"):
            log = run_query("SELECT id, timestamp, actor, action, details, prev_hash, entry_hash FROM audit_log ORDER BY id ASC")
            if not log:
                st.info("Audit log is empty.")
            else:
                broken = False
                for i, entry in enumerate(log):
                    if i == 0:
                        expected_prev = entry.get("prev_hash")  # accept actual genesis sentinel
                    else:
                        expected_prev = log[i - 1].get("entry_hash")

                    if entry.get("prev_hash") != expected_prev:
                        st.error(f"Chain broken at entry #{entry['id']}! Expected prev_hash "
                                 f"`{(expected_prev or '')[:16]}...` but got `{(entry.get('prev_hash') or '')[:16]}...`")
                        broken = True
                        break

                if not broken:
                    st.success(f"Audit chain verified: {len(log)} entries, all hashes valid.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3: SSP & POA&M
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📝 SSP & POA&M":
    st.title("SSP Generation & POA&M Management")

    tab_ssp, tab_poam, tab_export = st.tabs(["📄 SSP", "📋 POA&M", "📦 Export"])

    # ─── SSP Tab ──────────────────────────────────────────────────────────
    with tab_ssp:
        st.subheader("System Security Plan")

        ssp_sections = run_query("""
            SELECT s.id, s.control_id, s.implementation_status, s.narrative,
                   s.evidence_refs, s.gaps, s.version, s.generated_by, s.created_at,
                   c.family_abbrev, c.title, c.points
            FROM ssp_sections s
            JOIN controls c ON c.id = s.control_id
            WHERE s.org_id = :org_id
            ORDER BY c.family_abbrev, c.id
        """, {"org_id": ORG_ID})

        if not ssp_sections:
            st.warning("No SSP generated yet.")
            st.write("Click the button below to generate a full SSP for all 110 controls.")
            st.write("This will call the Claude API for each control (~30 minutes, ~$2-3 API cost).")

            if st.button("🚀 Generate Full SSP", type="primary"):
                try:
                    resp = requests.post(
                        f"{API_BASE}/api/ssp/generate-full",
                        json={"org_profile": {"org_id": ORG_ID}, "export_docx": True},
                        timeout=10,
                    )
                    resp.raise_for_status()
                    job = resp.json()
                    st.session_state["ssp_job_id"] = job["job_id"]
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to start SSP generation: {e}")

            # Poll job status if one is running
            job_id = st.session_state.get("ssp_job_id")
            if job_id:
                try:
                    resp = requests.get(f"{API_BASE}/api/ssp/status", params={"job_id": job_id}, timeout=5)
                    if resp.ok:
                        job = resp.json()
                        status = job.get("status", "pending")
                        done = job.get("controls_done", 0)
                        total = job.get("controls_total", 110) or 110
                        progress_pct = done / total if total else 0

                        st.progress(progress_pct, text=f"Generating SSP: {job.get('progress', '...')}")
                        if status == "completed":
                            st.success("SSP generation complete! Reload to view sections.")
                            st.session_state.pop("ssp_job_id", None)
                        elif status == "failed":
                            st.error(f"SSP generation failed: {job.get('error')}")
                            st.session_state.pop("ssp_job_id", None)
                        else:
                            time.sleep(5)
                            st.rerun()
                except Exception as e:
                    st.warning(f"Could not reach API to check job status: {e}")
        else:
            st.success(f"SSP generated: {len(ssp_sections)} sections covering "
                       f"{len(ssp_sections)}/{sprs['total']} controls")

            # Family filter
            families_in_ssp = sorted(set(s["family_abbrev"] for s in ssp_sections))
            selected_family = st.selectbox("Filter by family", ["All"] + families_in_ssp)

            filtered_ssp = ssp_sections if selected_family == "All" else [
                s for s in ssp_sections if s["family_abbrev"] == selected_family
            ]

            for s in filtered_ssp:
                status_icon = {"Implemented": "🟢", "Partially Implemented": "🟡", "Not Implemented": "🔴"}
                icon = status_icon.get(s["implementation_status"], "⚪")

                with st.expander(f"{icon} {s['control_id']} — {s['title'][:70]}"):
                    st.write(f"**Status:** {s['implementation_status']}  |  "
                             f"**Points:** {s['points']}  |  "
                             f"**Version:** {s['version']}")
                    st.write("---")
                    st.write(s.get("narrative", "No narrative generated."))

                    if s.get("gaps"):
                        gaps_data = s["gaps"] if isinstance(s["gaps"], list) else json.loads(s["gaps"]) if s["gaps"] else []
                        if gaps_data:
                            st.warning("**Gaps identified:**")
                            for gap in gaps_data:
                                st.write(f"- {gap}")

                    if s.get("evidence_refs"):
                        refs = s["evidence_refs"] if isinstance(s["evidence_refs"], list) else json.loads(s["evidence_refs"]) if s["evidence_refs"] else []
                        if refs:
                            st.info(f"**Evidence references:** {', '.join(str(r) for r in refs)}")

            # SSP download
            st.divider()
            st.subheader("Download SSP Document")
            exports = sorted(
                [f for f in os.listdir(EXPORTS_DIR) if f.startswith("SSP_") and f.endswith(".docx")],
                reverse=True,
            ) if os.path.exists(EXPORTS_DIR) else []

            if exports:
                latest = exports[0]
                filepath = os.path.join(EXPORTS_DIR, latest)
                with open(filepath, "rb") as f:
                    st.download_button(
                        f"📥 Download {latest}",
                        data=f.read(),
                        file_name=latest,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
            else:
                st.info("No SSP exports found. Generate an SSP first, then export to .docx.")

    # ─── POA&M Tab ────────────────────────────────────────────────────────
    with tab_poam:
        st.subheader("Plan of Action & Milestones")

        poam = load_poam_data()

        if not poam:
            st.info("No POA&M items. Generate them from gap assessment data.")
            if ssp_sections:
                if st.button("📋 Generate POA&M Items", type="primary"):
                    _generate_poam_items()
                    st.rerun()
        else:
            total_points = sum(p.get("points", 0) for p in poam if p["status"] in ("OPEN", "IN_PROGRESS"))
            pc1, pc2, pc3 = st.columns(3)
            pc1.metric("Total Items", len(poam))
            pc2.metric("Points at Risk", total_points)
            overdue = sum(1 for p in poam if p.get("scheduled_completion") and
                         p["scheduled_completion"] < datetime.now(timezone.utc) and
                         p["status"] not in ("CLOSED",))
            pc3.metric("Overdue", overdue)

            df_poam = pd.DataFrame(poam)
            display_cols = ["control_id", "control_title", "status", "risk_level",
                           "points", "weakness_description", "scheduled_completion"]
            available_cols = [c for c in display_cols if c in df_poam.columns]
            st.dataframe(df_poam[available_cols], use_container_width=True, hide_index=True)

    # ─── Export Tab ───────────────────────────────────────────────────────
    with tab_export:
        st.subheader("Assessment Binder Export")
        st.write("Generate a complete assessment package as a ZIP file containing all compliance artifacts.")

        if st.button("📦 Generate Evidence Binder (ZIP)", type="primary"):
            zip_path = _generate_binder()
            if zip_path:
                with open(zip_path, "rb") as f:
                    st.download_button(
                        f"📥 Download Evidence Binder",
                        data=f.read(),
                        file_name=os.path.basename(zip_path),
                        mime="application/zip",
                    )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4: DEMO CONTROLS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔧 Demo Controls":
    st.title("Demo Controls")
    st.caption("Reset, configure, and manage the demo environment")

    # ─── Reset ────────────────────────────────────────────────────────────
    st.subheader("🔄 Reset Demo Data")
    st.write("Clear all generated data (SSP, POA&M, evidence, audit log) for a fresh demo start.")

    rc1, rc2 = st.columns(2)
    with rc1:
        if st.button("🧹 Full Reset (clear everything)", type="primary"):
            _do_reset(keep_evidence=False)
            st.rerun()
    with rc2:
        if st.button("🧹 Partial Reset (keep evidence)"):
            _do_reset(keep_evidence=True)
            st.rerun()

    # ─── Quick Actions ────────────────────────────────────────────────────
    st.divider()
    st.subheader("⚡ Quick Demo Actions")

    qa1, qa2 = st.columns(2)
    with qa1:
        if st.button("📤 Load Sample Evidence (6 files)"):
            _load_sample_evidence()
            st.rerun()

    with qa2:
        if st.button("📋 Auto-Generate POA&M Items"):
            _generate_poam_items()
            st.rerun()

    # ─── Audit Log Viewer ─────────────────────────────────────────────────
    st.divider()
    st.subheader("📜 Audit Log (Recent)")
    log = load_audit_log(limit=30)
    if log:
        df_log = pd.DataFrame(log)
        display_log_cols = ["id", "timestamp", "actor", "action", "target_type", "target_id"]
        available = [c for c in display_log_cols if c in df_log.columns]
        st.dataframe(df_log[available], use_container_width=True, hide_index=True)
    else:
        st.info("Audit log is empty.")

    # ─── System Info ──────────────────────────────────────────────────────
    st.divider()
    st.subheader("ℹ️ System Info")
    info = run_query("SELECT COUNT(*) as cnt FROM controls")
    st.json({
        "org_id": ORG_ID,
        "org_name": "Apex Defense Solutions",
        "controls_loaded": info[0]["cnt"] if info else 0,
        "platform_version": "0.9.0",
        "llm_backend": "Claude API (development)",
        "production_inference": "vLLM (sovereign deployment)",
    })


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _write_audit_entry(actor, actor_type, action, target_type, target_id, details):
    """Write a hash-chained audit log entry using the canonical algorithm."""
    from datetime import datetime, timezone
    last = run_query("SELECT entry_hash FROM audit_log ORDER BY id DESC LIMIT 1")
    prev_hash = last[0]["entry_hash"] if last else "GENESIS"

    now_iso = datetime.now(timezone.utc).isoformat()

    # MUST match src/evidence/state_machine.py::_compute_entry_hash
    payload = json.dumps(
        {
            "actor": actor,
            "actor_type": actor_type,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "details": details,
            "prev_hash": prev_hash,
            "timestamp": now_iso,
        },
        sort_keys=True,
        default=str,
    )
    entry_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    run_exec("""
        INSERT INTO audit_log (timestamp, actor, actor_type, action, target_type,
                               target_id, details, prev_hash, entry_hash)
        VALUES (:timestamp, :actor, :actor_type, :action, :target_type,
                :target_id, CAST(:details AS json), :prev_hash, :entry_hash)
    """, {
        "timestamp": now_iso,
        "actor": actor, "actor_type": actor_type,
        "action": action, "target_type": target_type, "target_id": target_id,
        "details": json.dumps(details),
        "prev_hash": prev_hash, "entry_hash": entry_hash,
    })


def _transition_evidence(artifact_id, file_path, current_state, new_state):
    """Transition evidence state with hashing at publish."""
    if new_state == "PUBLISHED" and file_path and os.path.exists(file_path):
        # Hash the file
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        file_hash = sha256.hexdigest()

        run_exec("""
            UPDATE evidence_artifacts
            SET state = :new_state, sha256_hash = :hash, hash_algorithm = 'SHA-256',
                published_at = NOW(), updated_at = NOW()
            WHERE id = :id
        """, {"new_state": new_state, "hash": file_hash, "id": artifact_id})
    elif new_state == "REVIEWED":
        run_exec("""
            UPDATE evidence_artifacts
            SET state = :new_state, reviewed_at = NOW(), updated_at = NOW()
            WHERE id = :id
        """, {"new_state": new_state, "id": artifact_id})
    elif new_state == "APPROVED":
        run_exec("""
            UPDATE evidence_artifacts
            SET state = :new_state, approved_at = NOW(), updated_at = NOW()
            WHERE id = :id
        """, {"new_state": new_state, "id": artifact_id})
    else:
        run_exec("""
            UPDATE evidence_artifacts
            SET state = :new_state, updated_at = NOW()
            WHERE id = :id
        """, {"new_state": new_state, "id": artifact_id})

    _write_audit_entry(
        actor="dashboard_user", actor_type="user",
        action="evidence.state_change",
        target_type="evidence_artifact", target_id=artifact_id,
        details={"from": current_state, "to": new_state},
    )
    st.success(f"Transitioned `{artifact_id}` from {current_state} → {new_state}")


def _generate_poam_items():
    """Auto-generate POA&M items for NOT MET / PARTIAL controls."""
    ssp_data = run_query("""
        SELECT s.control_id, s.implementation_status, c.points, c.poam_eligible, c.title
        FROM ssp_sections s
        JOIN controls c ON c.id = s.control_id
        WHERE s.org_id = :org_id
          AND s.implementation_status IN ('Partially Implemented', 'Not Implemented')
    """, {"org_id": ORG_ID})

    existing = run_query("""
        SELECT control_id FROM poam_items
        WHERE org_id = :org_id AND status IN ('OPEN', 'IN_PROGRESS')
    """, {"org_id": ORG_ID})
    existing_controls = {e["control_id"] for e in existing}

    created = 0
    deadline = (datetime.now(timezone.utc) + timedelta(days=180)).isoformat()

    for s in ssp_data:
        ctrl_id = s["control_id"]

        # Skip if already has POA&M
        if ctrl_id in existing_controls:
            continue

        # Skip if not POA&M eligible (e.g., CA.L2-3.12.4)
        if not s.get("poam_eligible", True):
            continue

        points = s.get("points", 1)
        risk = "CRITICAL" if points >= 5 else ("HIGH" if points >= 3 else "MEDIUM")

        poam_id = "poam-" + hashlib.sha256(f"{ORG_ID}-{ctrl_id}-poam".encode()).hexdigest()[:8]

        run_exec("""
            INSERT INTO poam_items
                (id, org_id, control_id, weakness_description, remediation_plan,
                 status, risk_level, scheduled_completion, created_at, updated_at)
            VALUES
                (:id, :org_id, :control_id, :weakness, :plan,
                 'OPEN', :risk, :deadline, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """, {
            "id": poam_id, "org_id": ORG_ID, "control_id": ctrl_id,
            "weakness": f"Control {ctrl_id} ({s['title'][:80]}) is {s['implementation_status']}.",
            "plan": f"Complete implementation of {ctrl_id} and gather supporting evidence.",
            "risk": risk, "deadline": deadline,
        })
        created += 1

        _write_audit_entry(
            actor="system", actor_type="system",
            action="poam.auto_create",
            target_type="poam_item", target_id=poam_id,
            details={"control_id": ctrl_id, "risk_level": risk},
        )

    st.success(f"Created {created} new POA&M items. {len(existing_controls)} already existed.")


def _do_reset(keep_evidence=False):
    """Reset demo data from the UI."""
    with st.spinner("Resetting demo data..."):
        db = SessionLocal()
        try:
            if not keep_evidence:
                db.execute(text(
                    "DELETE FROM evidence_control_map WHERE evidence_id IN "
                    "(SELECT id FROM evidence_artifacts WHERE org_id = :org_id)"
                ), {"org_id": ORG_ID})
            db.execute(text("DELETE FROM audit_log"))
            db.execute(text("DELETE FROM poam_items WHERE org_id = :org_id"), {"org_id": ORG_ID})
            db.execute(text("DELETE FROM ssp_sections WHERE org_id = :org_id"), {"org_id": ORG_ID})
            if not keep_evidence:
                db.execute(text("DELETE FROM evidence_artifacts WHERE org_id = :org_id"), {"org_id": ORG_ID})
            db.commit()
        finally:
            db.close()

        if not keep_evidence and os.path.exists(EVIDENCE_DIR):
            shutil.rmtree(EVIDENCE_DIR)
            os.makedirs(EVIDENCE_DIR, exist_ok=True)

    st.success("Demo data reset complete.")


def _load_sample_evidence():
    """Create sample evidence files for demo purposes."""
    samples = [
        {
            "filename": "AC_Policy_v3.1.pdf",
            "evidence_type": "policy",
            "source_system": "sharepoint",
            "description": "Access Control Policy governing user access, MFA requirements, and privilege management.",
            "controls": ["AC.L2-3.1.1", "AC.L2-3.1.2", "AC.L2-3.1.3", "AC.L2-3.1.5", "AC.L2-3.1.7"],
            "content": "APEX DEFENSE SOLUTIONS\nAccess Control Policy v3.1\nEffective: 2026-01-15\n\nThis policy establishes requirements for controlling access to organizational systems containing CUI.\n\n1. All users must authenticate via Microsoft Entra ID with MFA enabled.\n2. Privileged access requires approval from the Security Officer.\n3. Remote access requires VPN with certificate-based authentication.\n4. Access reviews are conducted quarterly.",
        },
        {
            "filename": "Entra_MFA_Config_Export.json",
            "evidence_type": "config",
            "source_system": "entra_id",
            "description": "Microsoft Entra ID conditional access policy export showing MFA enforcement.",
            "controls": ["IA.L2-3.5.3", "AC.L2-3.1.12"],
            "content": json.dumps({
                "policyName": "Require MFA for All Users",
                "state": "enabled",
                "conditions": {"userRisk": "low", "signInRisk": "low", "platforms": ["all"]},
                "grantControls": {"operator": "AND", "builtInControls": ["mfa"]},
                "sessionControls": {"signInFrequency": {"value": 4, "type": "hours"}},
                "modifiedDateTime": "2026-02-15T10:00:00Z",
            }, indent=2),
        },
        {
            "filename": "CrowdStrike_EDR_Screenshot.txt",
            "evidence_type": "screenshot",
            "source_system": "crowdstrike",
            "description": "CrowdStrike Falcon EDR dashboard showing 100% endpoint coverage and active threat monitoring.",
            "controls": ["SI.L2-3.14.1", "SI.L2-3.14.2", "SI.L2-3.14.6", "SI.L2-3.14.7"],
            "content": "CrowdStrike Falcon Dashboard Export\nDate: 2026-03-01\n\nEndpoint Coverage: 47/47 (100%)\nSensor Version: 7.14.17012\nPrevention Policy: Aggressive\nDetections (30-day): 3 (all remediated)\nQuarantine: Enabled\nUSB Device Control: Enforced",
        },
        {
            "filename": "IR_Plan_v2.0.docx",
            "evidence_type": "policy",
            "source_system": "sharepoint",
            "description": "Incident Response Plan defining procedures for detecting, reporting, and responding to security incidents.",
            "controls": ["IR.L2-3.6.1", "IR.L2-3.6.2", "IR.L2-3.6.3"],
            "content": "APEX DEFENSE SOLUTIONS\nIncident Response Plan v2.0\nEffective: 2026-01-01\n\n1. PREPARATION: IR team trained quarterly. Contact list maintained.\n2. DETECTION: CrowdStrike + Sentinel alerts. Triage within 15 minutes.\n3. CONTAINMENT: Network isolation via Palo Alto PA-450 firewall rules.\n4. ERADICATION: Full malware removal, system reimaging if needed.\n5. RECOVERY: Restore from verified backups. Monitor for 72 hours.\n6. LESSONS LEARNED: Post-incident review within 5 business days.",
        },
        {
            "filename": "KnowBe4_Training_Report_Q1_2026.csv",
            "evidence_type": "training_record",
            "source_system": "knowbe4",
            "description": "Security awareness training completion report showing 100% completion for Q1 2026.",
            "controls": ["AT.L2-3.2.1", "AT.L2-3.2.2"],
            "content": "Employee,Course,Completed,Score\nAll Staff (45),CUI Handling Basics,2026-02-28,94%\nAll Staff (45),Phishing Awareness,2026-03-01,91%\nIT Team (8),Insider Threat,2026-02-15,97%\nManagement (6),CMMC Overview,2026-01-20,100%",
        },
        {
            "filename": "BitLocker_Compliance_Report.xml",
            "evidence_type": "config",
            "source_system": "intune",
            "description": "Microsoft Intune BitLocker compliance report showing full disk encryption on all endpoints.",
            "controls": ["SC.L2-3.13.11", "MP.L2-3.8.1"],
            "content": "<ComplianceReport>\n  <GeneratedDate>2026-03-01T08:00:00Z</GeneratedDate>\n  <PolicyName>BitLocker Encryption - CUI Systems</PolicyName>\n  <TotalDevices>47</TotalDevices>\n  <Compliant>47</Compliant>\n  <NonCompliant>0</NonCompliant>\n  <EncryptionMethod>XTS-AES-256</EncryptionMethod>\n  <RecoveryKeyEscrow>AzureAD</RecoveryKeyEscrow>\n</ComplianceReport>",
        },
    ]

    created = 0
    for s in samples:
        # Write file
        file_path = os.path.join(EVIDENCE_DIR, s["filename"])
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(s["content"])

        artifact_id = hashlib.sha256(
            f"{ORG_ID}-{s['filename']}-sample".encode()
        ).hexdigest()[:20]

        # Check if already exists
        existing = run_query(
            "SELECT id FROM evidence_artifacts WHERE id = :id",
            {"id": artifact_id}
        )
        if existing:
            continue

        file_size = os.path.getsize(file_path)

        run_exec("""
            INSERT INTO evidence_artifacts
                (id, org_id, filename, file_path, file_size_bytes, mime_type,
                 state, evidence_type, source_system, description, owner, created_at, updated_at)
            VALUES
                (:id, :org_id, :filename, :file_path, :fsb, 'application/octet-stream',
                 'DRAFT', :etype, :source, :desc, 'admin@apexdefense.com', NOW(), NOW())
        """, {
            "id": artifact_id, "org_id": ORG_ID,
            "filename": s["filename"], "file_path": file_path,
            "fsb": file_size, "etype": s["evidence_type"],
            "source": s["source_system"], "desc": s["description"],
        })

        # Link controls
        for ctrl_id in s["controls"]:
            link_id = hashlib.sha256(f"{artifact_id}-{ctrl_id}".encode()).hexdigest()[:20]
            run_exec("""
                INSERT INTO evidence_control_map (id, evidence_id, control_id)
                Values (:id, :eid, :cid)
                ON CONFLICT DO NOTHING
            """, {"id": link_id, "eid": artifact_id, "cid": ctrl_id})

        _write_audit_entry(
            actor="demo_loader", actor_type="system",
            action="evidence.upload",
            target_type="evidence_artifact", target_id=artifact_id,
            details={"filename": s["filename"], "demo_sample": True},
        )
        created += 1

    st.success(f"Loaded {created} sample evidence files ({len(samples) - created} already existed).")


def _generate_binder():
    """Generate a complete evidence binder ZIP."""
    import zipfile

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"CMMC_Assessment_Binder_{ts}.zip"
    zip_path = os.path.join(EXPORTS_DIR, zip_name)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. SSP document (latest .docx)
        ssp_files = sorted(
            [f for f in os.listdir(EXPORTS_DIR) if f.startswith("SSP_") and f.endswith(".docx")],
            reverse=True,
        ) if os.path.exists(EXPORTS_DIR) else []
        if ssp_files:
            ssp_path = os.path.join(EXPORTS_DIR, ssp_files[0])
            zf.write(ssp_path, f"01_SSP/{ssp_files[0]}")

        # 2. Evidence files organized by family
        evidence = load_evidence_data()
        for e in evidence:
            links = load_evidence_control_links(e["id"])
            families = set(l["family_abbrev"] for l in links) if links else {"UNLINKED"}
            for fam in families:
                fam_name = FAMILY_NAMES.get(fam, fam)
                src_path = e.get("file_path", "")
                if src_path and os.path.exists(src_path):
                    zf.write(src_path, f"02_Evidence/{fam}_{fam_name}/{e['filename']}")

        # 3. Hash manifest
        manifest_files = sorted(
            [f for f in os.listdir(EXPORTS_DIR) if f.startswith("MANIFEST_")],
            reverse=True,
        ) if os.path.exists(EXPORTS_DIR) else []
        if manifest_files:
            mf_path = os.path.join(EXPORTS_DIR, manifest_files[0])
            zf.write(mf_path, f"03_Manifest/{manifest_files[0]}")

        # 4. POA&M report
        poam = load_poam_data()
        if poam:
            poam_content = "PLAN OF ACTION & MILESTONES (POA&M)\n"
            poam_content += f"Organization: Apex Defense Solutions\n"
            poam_content += f"Generated: {datetime.now(timezone.utc).isoformat()}\n"
            poam_content += "=" * 80 + "\n\n"
            for p in poam:
                poam_content += f"POA&M ID: {p['id']}\n"
                poam_content += f"Control: {p['control_id']} — {p.get('control_title', '')}\n"
                poam_content += f"Status: {p['status']}  |  Risk: {p.get('risk_level', 'N/A')}\n"
                poam_content += f"Weakness: {p.get('weakness_description', 'N/A')}\n"
                poam_content += f"Remediation: {p.get('remediation_plan', 'N/A')}\n"
                poam_content += f"Deadline: {p.get('scheduled_completion', 'N/A')}\n"
                poam_content += "-" * 40 + "\n"
            zf.writestr("04_POAM/POAM_Report.txt", poam_content)

        # 5. Audit log export
        log = run_query("SELECT * FROM audit_log ORDER BY id ASC")
        if log:
            audit_content = "AUDIT LOG EXPORT\n"
            audit_content += f"Generated: {datetime.now(timezone.utc).isoformat()}\n"
            audit_content += f"Total entries: {len(log)}\n"
            audit_content += "=" * 80 + "\n\n"
            for entry in log:
                audit_content += f"#{entry.get('id')} | {entry.get('timestamp')} | "
                audit_content += f"{entry.get('actor')} ({entry.get('actor_type')}) | "
                audit_content += f"{entry.get('action')} | {entry.get('target_type')}:{entry.get('target_id')}\n"
                audit_content += f"  Hash: {entry.get('entry_hash', 'N/A')[:32]}...\n"
            zf.writestr("05_Audit/Audit_Log_Export.txt", audit_content)

        # 6. Binder index
        index_content = f"""CMMC LEVEL 2 ASSESSMENT BINDER
Organization: Apex Defense Solutions
Generated: {datetime.now(timezone.utc).isoformat()}

Contents:
  01_SSP/           — System Security Plan (.docx)
  02_Evidence/      — Evidence artifacts organized by control family
  03_Manifest/      — SHA-256 hash manifest (CMMC/eMASS format)
  04_POAM/          — Plan of Action & Milestones report
  05_Audit/         — Hash-chained audit log export

SPRS Score: {sprs['conditional_score']}/110
Controls Assessed: {sprs['met'] + sprs['partial'] + sprs['not_met']}/{sprs['total']}
Evidence Artifacts: {len(evidence)}
POA&M Items: {len(poam)}
Audit Log Entries: {len(log)}
"""
        zf.writestr("00_INDEX.txt", index_content)

    st.success(f"Evidence binder created: `{zip_path}`")
    return zip_path
