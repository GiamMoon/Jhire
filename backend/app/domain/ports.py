"""
JHIRE 2026 — Domain Ports (Hexagonal Architecture)
===================================================
Abstract interfaces (ports) that define the contracts between
the domain/use_cases layer and the infrastructure layer.

This ensures the domain layer is NEVER coupled to specific
database implementations (SQLAlchemy, PostgreSQL, etc.).
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime


class UserRepositoryPort(ABC):
    """Port for User data access — implemented by infrastructure."""

    @abstractmethod
    def get_by_id(self, user_id: int):
        """Retrieve a user by their primary key."""
        ...

    @abstractmethod
    def get_by_email(self, email: str):
        """Retrieve a user by their email address."""
        ...

    @abstractmethod
    def create(self, user_data) -> object:
        """Persist a new user and return the created entity."""
        ...

    @abstractmethod
    def update(self, user_id: int, update_data: dict) -> object:
        """Update user fields and return the updated entity."""
        ...


class ProductRepositoryPort(ABC):
    """Port for Product data access."""

    @abstractmethod
    def get_all(self, category: Optional[str] = None) -> List:
        """Retrieve all products, optionally filtered by category."""
        ...

    @abstractmethod
    def get_by_id(self, product_id: int):
        """Retrieve a single product by its ID."""
        ...

    @abstractmethod
    def get_in_stock(self) -> List:
        """Retrieve all products with stock > 0."""
        ...

    @abstractmethod
    def update_stock(self, product_id: int, quantity_delta: int):
        """Atomically adjust a product's stock by delta."""
        ...


class OrderRepositoryPort(ABC):
    """Port for Order data access."""

    @abstractmethod
    def get_by_id(self, order_id: int):
        ...

    @abstractmethod
    def get_by_user(self, user_id: int) -> List:
        ...

    @abstractmethod
    def create(self, user_id: int, items: List[dict]) -> object:
        ...

    @abstractmethod
    def update_status(self, order_id: int, status: str):
        ...


class InvoiceRepositoryPort(ABC):
    """Port for Invoice / Billing data access."""

    @abstractmethod
    def get_by_id(self, invoice_id: int):
        ...

    @abstractmethod
    def create(self, order_id: int, client_ruc_dni: str, client_name: str) -> object:
        ...

    @abstractmethod
    def get_next_invoice_number(self) -> str:
        ...


class ProductViewRepositoryPort(ABC):
    """Port for product view tracking (Personalization/IA)."""

    @abstractmethod
    def track_view(self, user_id: int, product_id: int):
        """Register or increment a product view for a user."""
        ...

    @abstractmethod
    def get_user_views(self, user_id: int) -> List:
        """Get all product views for a specific user."""
        ...

    @abstractmethod
    def get_trending(self, since: datetime, limit: int) -> List:
        """Get globally trending products since a given date."""
        ...


class CRMRepositoryPort(ABC):
    """Port for CRM interactions data access."""

    @abstractmethod
    def log_interaction(self, user_id: int, interaction_type: str, notes: str):
        ...

    @abstractmethod
    def get_interactions(self, user_id: int) -> List:
        ...


class EmailServicePort(ABC):
    """Port for email sending — decouples domain from SMTP details."""

    @abstractmethod
    def send_email(self, to_email: str, subject: str, content: str):
        """Send an email asynchronously."""
        ...
