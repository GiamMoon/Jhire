"""
JHIRE 2026 — Product View Repository (Infrastructure Adapter)
==============================================================
Implements ProductViewRepositoryPort for the IA Personalization engine.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime
from ..models import ProductView, Product
from ...domain.ports import ProductViewRepositoryPort


class ProductViewRepository(ProductViewRepositoryPort):
    """Concrete adapter for product view tracking via SQLAlchemy."""

    def __init__(self, db: Session):
        self.db = db

    def track_view(self, user_id: int, product_id: int) -> ProductView:
        existing = self.db.query(ProductView).filter(
            ProductView.user_id == user_id,
            ProductView.product_id == product_id
        ).first()

        if existing:
            existing.view_count += 1
            existing.last_viewed = datetime.utcnow()
        else:
            existing = ProductView(
                user_id=user_id,
                product_id=product_id,
                view_count=1,
                first_viewed=datetime.utcnow(),
                last_viewed=datetime.utcnow()
            )
            self.db.add(existing)

        self.db.commit()
        self.db.refresh(existing)
        return existing

    def get_user_views(self, user_id: int) -> List[ProductView]:
        return self.db.query(ProductView).filter(
            ProductView.user_id == user_id
        ).all()

    def get_trending(self, since: datetime, limit: int = 8) -> List:
        return self.db.query(
            ProductView.product_id,
            func.sum(ProductView.view_count).label("total_views")
        ).filter(
            ProductView.last_viewed >= since
        ).group_by(
            ProductView.product_id
        ).order_by(
            desc("total_views")
        ).limit(limit).all()
