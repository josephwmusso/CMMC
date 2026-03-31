"""
Contact form endpoint for demo requests.
POST /api/contact — public, no auth required.
"""
import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/contact", tags=["Contact"])


class ContactRequest(BaseModel):
    name: str
    email: str
    company: str = ""
    employee_count: str = ""
    message: str = ""


@router.post("")
def submit_contact(req: ContactRequest, db: Session = Depends(get_db)):
    """Accept a demo request / contact form submission."""
    contact_id = f"CTR-{uuid.uuid4().hex[:12].upper()}"
    db.execute(text("""
        INSERT INTO contact_requests (id, name, email, company, employee_count, message, created_at, status)
        VALUES (:id, :name, :email, :company, :employee_count, :message, :now, 'new')
    """), {
        "id": contact_id,
        "name": req.name,
        "email": req.email,
        "company": req.company,
        "employee_count": req.employee_count,
        "message": req.message,
        "now": datetime.now(timezone.utc),
    })
    db.commit()
    logger.info(f"New contact request: {req.email} ({req.company})")
    return {"id": contact_id, "status": "received"}
