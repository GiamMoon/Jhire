from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from ...infrastructure.database import get_db
from ...infrastructure.repositories.user_repository import UserRepository
from ...use_cases.auth_service import AuthService
from ...domain.schemas import UserResponse, UserCreate, Token, UserUpdate
from ...infrastructure.security import get_current_user, pwd_context
from ...infrastructure.models import User
from ...infrastructure.email import send_async_email

router = APIRouter()

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    repo = UserRepository(db)
    return AuthService(repo)

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, background_tasks: BackgroundTasks, auth_service: AuthService = Depends(get_auth_service)):
    new_user = auth_service.register_user(user)
    
    # Send CRM Welcome Email
    welcome_content = f"Hola {new_user.first_name or new_user.email},\n\nBienvenido a JHIRE 2026. Gracias por registrarte. Nuestro equipo comercial se pondrá en contacto pronto."
    send_async_email(
        background_tasks=background_tasks, 
        to_email=user.email, 
        subject="¡Bienvenido a JHIRE 2026!", 
        content=welcome_content
    )
    
    return new_user

@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.authenticate_user(form_data.username, form_data.password)

@router.put("/profile", response_model=Token)
def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.update_user_profile(current_user.id, user_update)

# ─── NEW: Admin User Management ──────────────────────────────────────────────

class UserAdminResponse(BaseModel):
    id: int
    email: str
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    role: str
    data_protection_consent: bool
    profile_picture_url: str | None = None
    class Config:
        from_attributes = True

class RoleUpdate(BaseModel):
    role: str

class PasswordReset(BaseModel):
    password: str

@router.get("/users", response_model=List[UserAdminResponse])
def list_all_users(db: Session = Depends(get_db)):
    """List all users in the system (admin panel)."""
    return db.query(User).order_by(User.id).all()

@router.get("/me", response_model=UserAdminResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current logged-in user profile."""
    return current_user

@router.put("/users/{user_id}/role", response_model=UserAdminResponse)
def update_user_role(user_id: int, data: RoleUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Change a user's role (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden cambiar roles")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if data.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Rol inválido. Use 'admin' o 'user'")
    user.role = data.role
    db.commit()
    db.refresh(user)
    return user

@router.put("/users/{user_id}/reset-password")
def reset_user_password(user_id: int, data: PasswordReset, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Reset a user's password (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden resetear contraseñas")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.hashed_password = pwd_context.hash(data.password)
    db.commit()
    return {"detail": "Contraseña actualizada exitosamente"}

@router.put("/users/{user_id}", response_model=UserAdminResponse)
def update_user_data(user_id: int, data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update a user's profile data (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden editar usuarios")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.email is not None:
        user.email = data.email
    if data.phone is not None:
        user.phone = data.phone
    db.commit()
    db.refresh(user)
    return user

