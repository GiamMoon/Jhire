"""
JHIRE 2026 — Order Repository (Infrastructure Adapter)
=======================================================
Implements OrderRepositoryPort using SQLAlchemy + PostgreSQL.
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import Order, OrderItem, Product
from ...domain.ports import OrderRepositoryPort


class OrderRepository(OrderRepositoryPort):
    """Concrete adapter for Order data access via SQLAlchemy."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, order_id: int) -> Optional[Order]:
        return self.db.query(Order).filter(Order.id == order_id).first()

    def get_by_user(self, user_id: int) -> List[Order]:
        return self.db.query(Order).filter(
            Order.user_id == user_id
        ).order_by(Order.created_at.desc()).all()

    def create(self, user_id: int, items: List[dict]) -> Order:
        order = Order(user_id=user_id, total_price=0.0)
        self.db.add(order)
        self.db.flush()

        total = 0.0
        for item_data in items:
            product = self.db.query(Product).filter(
                Product.id == item_data["product_id"]
            ).first()
            if not product:
                continue
            unit_price = product.price_soles
            qty = item_data["quantity"]
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=qty,
                unit_price=unit_price
            )
            self.db.add(order_item)
            total += unit_price * qty

        order.total_price = total
        self.db.commit()
        self.db.refresh(order)
        return order

    def update_status(self, order_id: int, status: str) -> Optional[Order]:
        order = self.get_by_id(order_id)
        if order:
            order.status = status
            self.db.commit()
            self.db.refresh(order)
        return order
