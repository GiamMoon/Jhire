from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...infrastructure.database import get_db
from ...infrastructure.repositories.user_repository import UserRepository
from ...use_cases.auth_service import AuthService
from ...domain.schemas import UserResponse, UserCreate, Token

router = APIRouter()

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    repo = UserRepository(db)
    return AuthService(repo)

from fastapi import APIRouter, Depends, BackgroundTasks
from ...infrastructure.email import send_async_email

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

from ...infrastructure.security import get_current_user
from ...infrastructure.models import User
from ...domain.schemas import UserUpdate

@router.put("/profile", response_model=Token)
def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.update_user_profile(current_user.id, user_update)
