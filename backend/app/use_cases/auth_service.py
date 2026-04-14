from fastapi import HTTPException, status
from datetime import timedelta
from ..infrastructure.repositories.user_repository import UserRepository
from ..domain.schemas import UserCreate, UserUpdate, Token
from ..infrastructure.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def register_user(self, user_data: UserCreate):
        if self.user_repo.get_user_by_email(user_data.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        return self.user_repo.create_user(user_data)

    def update_user_profile(self, user_id: int, update_data: UserUpdate) -> Token:
        from ..infrastructure.models import User
        from ..infrastructure.security import get_password_hash
        
        user = self.user_repo.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        update_dict = update_data.model_dump(exclude_unset=True)
        if "email" in update_dict and update_dict["email"] != user.email:
            if self.user_repo.get_user_by_email(update_dict["email"]):
                raise HTTPException(status_code=400, detail="El correo ya se encuentra en uso")

        for key, value in update_dict.items():
            if key == "password":
                user.hashed_password = get_password_hash(value)
            else:
                setattr(user, key, value)

        self.user_repo.db.commit()
        self.user_repo.db.refresh(user)

        # Generate new token automatically
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.email, 
                "role": user.role, 
                "first_name": user.first_name, 
                "last_name": user.last_name,
                "profile_picture_url": user.profile_picture_url
            }, 
            expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer", role=user.role)

    def authenticate_user(self, email: str, password: str) -> Token:
        user = self.user_repo.get_user_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.email, 
                "role": user.role, 
                "first_name": user.first_name, 
                "last_name": user.last_name,
                "profile_picture_url": user.profile_picture_url
            }, 
            expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer", role=user.role)
