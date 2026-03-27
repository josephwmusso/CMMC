"""
src/api/document_routes.py
FastAPI routes for the document generation engine.

Endpoints:
  GET    /api/documents/templates         — List all document templates
  GET    /api/documents/templates/{type}   — Get template details
  POST   /api/documents/generate/{type}    — Generate a document
  GET    /api/documents                    — List generated documents for org
  GET    /api/documents/{id}               — Get generated document with sections
  GET    /api/documents/{id}/download      — Download DOCX
  POST   /api/documents/generate-all       — Generate all applicable documents
"""

import json
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import text

from src.db.session import get_session
from src.documents.generator import DocumentGenerator
from src.documents.docx_builder import build_docx

router = APIRouter(prefix="/api/documents", tags=["documents"])

ORG_ID = "9de53b587b23450b87af"


@router.get("/templates")
async def list_templates():
    """List all document templates."""
    with get_session() as db:
        rows = db.execute(text("""
            SELECT doc_type, title, description, conditional_on,
                   estimated_pages, control_ids
            FROM document_templates ORDER BY doc_type
        """)).fetchall()

    return {
        "templates": [
            {
                "doc_type": r[0],
                "title": r[1],
                "description": r[2],
                "conditional": r[3] is not None,
                "conditional_on": r[3],
                "estimated_pages": r[4],
                "control_count": len(r[5]) if isinstance(r[5], list) else len(json.loads(r[5] or "[]")),
            }
            for r in rows
        ]
    }


@router.get("/templates/{doc_type}")
async def get_template(doc_type: str):
    """Get full template details including section structure."""
    with get_session() as db:
        row = db.execute(text("""
            SELECT id, doc_type, title, description, sections,
                   control_ids, conditional_on, estimated_pages
            FROM document_templates WHERE doc_type = :dt
        """), {"dt": doc_type}).fetchone()

    if not row:
        raise HTTPException(404, f"Template '{doc_type}' not found")

    sections = row[4] if isinstance(row[4], list) else json.loads(row[4])

    return {
        "id": row[0],
        "doc_type": row[1],
        "title": row[2],
        "description": row[3],
        "sections": sections,
        "control_ids": row[5] if isinstance(row[5], list) else json.loads(row[5] or "[]"),
        "conditional_on": row[6],
        "estimated_pages": row[7],
    }


@router.post("/generate/{doc_type}")
async def generate_document(doc_type: str):
    """Generate a single document from template + intake answers."""
    gen = DocumentGenerator(org_id=ORG_ID)

    try:
        template = gen.get_template(doc_type)
    except ValueError:
        raise HTTPException(404, f"Template '{doc_type}' not found")

    result = gen.generate_document(doc_type)

    # Build DOCX
    profile = gen.get_company_profile()
    company_name = profile.get("company_name") or "Organization"

    filepath = build_docx(
        title=template["title"],
        company_name=company_name,
        sections=result["sections"],
        output_dir="data/exports",
        doc_type=doc_type,
    )

    # Update file_path in generated_documents
    with get_session() as db:
        db.execute(text("""
            UPDATE generated_documents SET file_path = :fp, updated_at = :now
            WHERE id = :did
        """), {"fp": filepath, "now": datetime.now(timezone.utc).isoformat(), "did": result["doc_id"]})
        db.commit()

    # Create evidence artifact
    control_ids = template.get("control_ids", [])
    if not control_ids:
        for sec in template.get("sections", []):
            control_ids.extend(sec.get("control_ids", []))
        control_ids = sorted(set(control_ids))

    artifact_id = gen.create_evidence_artifact(
        doc_id=result["doc_id"],
        doc_type=doc_type,
        title=template["title"],
        file_path=filepath,
        control_ids=control_ids,
    )

    return {
        "doc_id": result["doc_id"],
        "title": result["title"],
        "doc_type": doc_type,
        "word_count": result["word_count"],
        "section_count": len(result["sections"]),
        "file_path": filepath,
        "evidence_artifact_id": artifact_id,
        "status": "draft",
        "message": "Document generated. Review and approve before publishing as evidence.",
    }


@router.get("")
async def list_generated_documents():
    """List all generated documents for the org."""
    with get_session() as db:
        rows = db.execute(text("""
            SELECT id, doc_type, title, version, status, word_count,
                   file_path, evidence_artifact_id, created_at, updated_at
            FROM generated_documents
            WHERE org_id = :org_id
            ORDER BY created_at DESC
        """), {"org_id": ORG_ID}).fetchall()

    return {
        "documents": [
            {
                "id": r[0], "doc_type": r[1], "title": r[2],
                "version": r[3], "status": r[4], "word_count": r[5],
                "has_file": bool(r[6]), "evidence_artifact_id": r[7],
                "created_at": r[8], "updated_at": r[9],
            }
            for r in rows
        ]
    }


@router.get("/{doc_id}")
async def get_document(doc_id: str):
    """Get a generated document with its sections."""
    with get_session() as db:
        row = db.execute(text("""
            SELECT id, doc_type, title, version, status, sections_data,
                   word_count, file_path, evidence_artifact_id, created_at
            FROM generated_documents WHERE id = :did
        """), {"did": doc_id}).fetchone()

    if not row:
        raise HTTPException(404, "Document not found")

    sections = row[5] if isinstance(row[5], list) else json.loads(row[5] or "[]")

    return {
        "id": row[0], "doc_type": row[1], "title": row[2],
        "version": row[3], "status": row[4], "sections": sections,
        "word_count": row[6], "file_path": row[7],
        "evidence_artifact_id": row[8], "created_at": row[9],
    }


@router.get("/{doc_id}/download")
async def download_document(doc_id: str):
    """Download the DOCX file for a generated document."""
    with get_session() as db:
        row = db.execute(text("""
            SELECT file_path, title FROM generated_documents WHERE id = :did
        """), {"did": doc_id}).fetchone()

    if not row or not row[0]:
        raise HTTPException(404, "Document file not found")

    if not os.path.exists(row[0]):
        raise HTTPException(404, f"File not found on disk: {row[0]}")

    return FileResponse(
        row[0],
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=os.path.basename(row[0]),
    )


@router.post("/generate-all")
async def generate_all_documents():
    """Generate all applicable documents based on intake answers."""
    gen = DocumentGenerator(org_id=ORG_ID)
    answers = gen.get_intake_answers()

    # Get all templates
    with get_session() as db:
        rows = db.execute(text("""
            SELECT doc_type, conditional_on, conditional_values
            FROM document_templates ORDER BY doc_type
        """)).fetchall()

    results = []
    skipped = []

    for row in rows:
        doc_type = row[0]
        conditional_on = row[1]
        conditional_values = row[2] if isinstance(row[2], list) else json.loads(row[2] or "[]")

        # Check conditional
        if conditional_on:
            answer = answers.get(conditional_on, "")
            # For multiple choice, check if any conditional value is in the answer
            if conditional_values:
                match = False
                for cv in conditional_values:
                    if cv in answer:
                        match = True
                        break
                if not match:
                    skipped.append({"doc_type": doc_type, "reason": f"Conditional on {conditional_on} not met"})
                    continue

        try:
            result = gen.generate_document(doc_type)

            # Build DOCX
            template = gen.get_template(doc_type)
            profile = gen.get_company_profile()
            company_name = profile.get("company_name") or "Organization"

            filepath = build_docx(
                title=template["title"],
                company_name=company_name,
                sections=result["sections"],
                output_dir="data/exports",
                doc_type=doc_type,
            )

            # Update file path
            with get_session() as db:
                db.execute(text("""
                    UPDATE generated_documents SET file_path = :fp, updated_at = :now WHERE id = :did
                """), {"fp": filepath, "now": datetime.now(timezone.utc).isoformat(), "did": result["doc_id"]})
                db.commit()

            # Create evidence artifact
            control_ids = template.get("control_ids", [])
            if not control_ids:
                for sec in template.get("sections", []):
                    control_ids.extend(sec.get("control_ids", []))
                control_ids = sorted(set(control_ids))

            artifact_id = gen.create_evidence_artifact(
                doc_id=result["doc_id"],
                doc_type=doc_type,
                title=template["title"],
                file_path=filepath,
                control_ids=control_ids,
            )

            results.append({
                "doc_type": doc_type,
                "title": result["title"],
                "doc_id": result["doc_id"],
                "word_count": result["word_count"],
                "evidence_artifact_id": artifact_id,
            })
        except Exception as e:
            results.append({"doc_type": doc_type, "error": str(e)})

    return {
        "generated": len([r for r in results if "error" not in r]),
        "errors": len([r for r in results if "error" in r]),
        "skipped": len(skipped),
        "results": results,
        "skipped_details": skipped,
    }
