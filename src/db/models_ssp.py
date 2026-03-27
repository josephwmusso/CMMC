"""
src/db/models_ssp.py

SSPSection model for persisting generated SSP narratives.

ADD THIS CLASS to your existing src/db/models.py, or import from here.

If adding to models.py, place it after the existing model classes and add:
    from sqlalchemy.dialects.postgresql import JSONB
to the imports at the top.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

# Import Base from your existing models
from src.db.models import Base


class SSPSection(Base):
    """SSP narrative per control per organization.

    Each row stores the AI-generated implementation narrative,
    evidence references, gaps, and version info.
    """
    __tablename__ = "ssp_sections"

    id = Column(String(20), primary_key=True)
    control_id = Column(String(30), ForeignKey("controls.id"), nullable=False)
    org_id = Column(String(100), nullable=False, default="default-org")
    narrative = Column(Text, nullable=False, default="")
    implementation_status = Column(String(30), nullable=False, default="Not Implemented")
    evidence_refs = Column(JSONB, default=[])
    gaps = Column(JSONB, default=[])
    generated_by = Column(String(50), default="ssp_agent")
    version = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Unique constraint: one section per control per org
    __table_args__ = {"extend_existing": True}

    def __repr__(self):
        return f"<SSPSection {self.control_id} org={self.org_id} v{self.version} status={self.implementation_status}>"
