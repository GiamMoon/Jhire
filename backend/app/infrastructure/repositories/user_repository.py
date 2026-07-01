"""
JHIRE 2026 — User Repository (Infrastructure Adapter)
======================================================
Implements UserRepositoryPort using SQLAlchemy + PostgreSQL.
Follows Hexagonal Architecture: domain depends on the PORT,
not on this concrete adapter.
"""

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from typing import Optional
from ..models import User
from ...domain.schemas import UserCreate
from ...domain.ports import UserRepositoryPort
from ..security import get_password_hash


class UserRepository(UserRepositoryPort):
    """Concrete adapter for User data access via SQLAlchemy."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    # Legacy alias for backward compatibility with AuthService
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.get_by_email(email)

    def create(self, user_data) -> User:
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            data_protection_consent=user_data.data_protection_consent
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    # Legacy alias for backward compatibility with AuthService
    def create_user(self, user: UserCreate) -> User:
        return self.create(user)

    def update(self, user_id: int, update_data: dict) -> Optional[User]:
        user = self.get_by_id(user_id)
        if not user:
            return None
        for key, value in update_data.items():
            if key == "password":
                user.hashed_password = get_password_hash(value)
            else:
                setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user
