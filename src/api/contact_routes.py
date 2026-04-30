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

    try:
        from configs.settings import RESEND_API_KEY, EMAIL_FROM, CONTACT_FORM_RECIPIENTS
        if RESEND_API_KEY:
            import resend
            resend.api_key = RESEND_API_KEY
            resend.Emails.send({
                "from": f"Intranest Notifications <{EMAIL_FROM}>",
                "to": CONTACT_FORM_RECIPIENTS,
                "subject": f"New contact: {req.name}",
                "html": f"""
                    <h2>New Intranest Contact Form Submission</h2>
                    <table style="border-collapse: collapse; font-family: sans-serif;">
                        <tr>
                            <td style="padding: 8px 16px 8px 0; font-weight: bold; color: #666;">Name</td>
                            <td style="padding: 8px 0;">{req.name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 16px 8px 0; font-weight: bold; color: #666;">Email</td>
                            <td style="padding: 8px 0;"><a href="mailto:{req.email}">{req.email}</a></td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 16px 8px 0; font-weight: bold; color: #666;">Company</td>
                            <td style="padding: 8px 0;">{req.company or "—"}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 16px 8px 0; font-weight: bold; color: #666;">Size</td>
                            <td style="padding: 8px 0;">{req.employee_count or "—"}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 16px 8px 0; font-weight: bold; color: #666;">Message</td>
                            <td style="padding: 8px 0;">{req.message or "—"}</td>
                        </tr>
                    </table>
                    <p style="margin-top: 24px; color: #999; font-size: 12px;">
                        Submitted via intranest.ai contact form
                    </p>
                """,
            })
    except Exception as e:
        logger.warning(f"Contact notification email failed: {e}")

    return {"id": contact_id, "status": "received"}
