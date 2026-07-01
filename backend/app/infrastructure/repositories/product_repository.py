"""
JHIRE 2026 — Product Repository (Infrastructure Adapter)
=========================================================
Implements ProductRepositoryPort using SQLAlchemy + PostgreSQL.
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import Product
from ...domain.ports import ProductRepositoryPort


class ProductRepository(ProductRepositoryPort):
    """Concrete adapter for Product data access via SQLAlchemy."""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self, category: Optional[str] = None) -> List[Product]:
        query = self.db.query(Product)
        if category:
            query = query.filter(Product.category == category)
        return query.all()

    def get_by_id(self, product_id: int) -> Optional[Product]:
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_in_stock(self) -> List[Product]:
        return self.db.query(Product).filter(Product.stock > 0).all()

    def update_stock(self, product_id: int, quantity_delta: int) -> Optional[Product]:
        product = self.get_by_id(product_id)
        if product:
            product.stock += quantity_delta
            self.db.commit()
            self.db.refresh(product)
        return product
