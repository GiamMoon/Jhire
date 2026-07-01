"""
JHIRE 2026 — CRM Repository (Infrastructure Adapter)
=====================================================
Implements CRMRepositoryPort using SQLAlchemy + PostgreSQL.
"""

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import desc
from typing import List
from datetime import datetime
from ..models import CRMInteraction
from ...domain.ports import CRMRepositoryPort


class CRMRepository(CRMRepositoryPort):
    """Concrete adapter for CRM interaction data access via SQLAlchemy."""

    def __init__(self, db: Session):
        self.db = db

    def log_interaction(self, user_id: int, interaction_type: str, notes: str) -> CRMInteraction:
        interaction = CRMInteraction(
            user_id=user_id,
            type=interaction_type,
            notes=notes,
            date=datetime.utcnow()
        )
        self.db.add(interaction)
        self.db.commit()
        self.db.refresh(interaction)
        return interaction

    def get_interactions(self, user_id: int) -> List[CRMInteraction]:
        return self.db.query(CRMInteraction).filter(
            CRMInteraction.user_id == user_id
        ).order_by(desc(CRMInteraction.date)).all()
