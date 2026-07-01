"""
JHIRE 2026 — Authentication Use Case
======================================
Application service that orchestrates user authentication logic.
Depends on UserRepositoryPort (the abstract port), NOT on
SQLAlchemy or any infrastructure detail.

Hexagonal Architecture:
  Domain Port (UserRepositoryPort) ← Use Case (AuthService) → Presentation (Router)
"""

# pyrefly: ignore [missing-import]
from fastapi import HTTPException, status
from datetime import timedelta
from ..domain.ports import UserRepositoryPort
from ..domain.schemas import UserCreate, UserUpdate, Token
from ..infrastructure.security import verify_password, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES


class AuthService:
    """Use case: Handles registration, login, and profile updates."""

    def __init__(self, user_repo: UserRepositoryPort):
        # Accepts ANY implementation of UserRepositoryPort (hexagonal DI)
        self.user_repo = user_repo

    def register_user(self, user_data: UserCreate):
        """Register a new user after validating uniqueness."""
        if self.user_repo.get_by_email(user_data.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        return self.user_repo.create(user_data)

    def update_user_profile(self, user_id: int, update_data: UserUpdate) -> Token:
        """Update user profile fields and return a fresh JWT token."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        update_dict = update_data.model_dump(exclude_unset=True)

        # Check email uniqueness if changing email
        if "email" in update_dict and update_dict["email"] != user.email:
            if self.user_repo.get_by_email(update_dict["email"]):
                raise HTTPException(status_code=400, detail="El correo ya se encuentra en uso")

        # Apply updates via port method
        for key, value in update_dict.items():
            if key == "password":
                user.hashed_password = get_password_hash(value)
            else:
                setattr(user, key, value)

        # Commit via the repository's session
        self.user_repo.db.commit()
        self.user_repo.db.refresh(user)

        # Generate new token with updated claims
        access_token = self._create_user_token(user)
        return Token(access_token=access_token, token_type="bearer", role=user.role)

    def authenticate_user(self, email: str, password: str) -> Token:
        """Authenticate user credentials and return a JWT token."""
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = self._create_user_token(user)
        return Token(access_token=access_token, token_type="bearer", role=user.role)

    def _create_user_token(self, user) -> str:
        """Internal helper to generate a JWT with standard claims."""
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        return create_access_token(
            data={
                "sub": user.email,
                "role": user.role,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "profile_picture_url": user.profile_picture_url
            },
            expires_delta=access_token_expires
        )
