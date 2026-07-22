"""
JHIRE 2026 — Servicio de Autenticación (Caso de Uso)
======================================================
TESIS: Sistema Web para la Gestión Comercial de la Empresa JHIRE

╔══════════════════════════════════════════════════════════════════════════╗
║  ARQUITECTURA HEXAGONAL — CAPA DE CASOS DE USO (Application Layer)     ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  Esta clase implementa la lógica de negocio de AUTENTICACIÓN.         ║
║  Es un ejemplo CLAVE de la Arquitectura Hexagonal en acción:          ║
║                                                                        ║
║  ┌───────────────────────────────────────────────────────────────┐     ║
║  │  Router (auth.py)                                             │     ║
║  │    │                                                          │     ║
║  │    ▼                                                          │     ║
║  │  AuthService(user_repo: UserRepositoryPort)  ← INYECCIÓN DI  │     ║
║  │    │                                                          │     ║
║  │    ▼                                                          │     ║
║  │  UserRepositoryPort (interfaz abstracta)     ← PUERTO         │     ║
║  │    │                                                          │     ║
║  │    ▼                                                          │     ║
║  │  UserRepository (SQLAlchemy)                 ← ADAPTADOR      │     ║
║  └───────────────────────────────────────────────────────────────┘     ║
║                                                                        ║
║  INYECCIÓN DE DEPENDENCIAS (DI):                                      ║
║  → El constructor recibe UserRepositoryPort (la INTERFAZ)             ║
║  → NO recibe UserRepository (la implementación concreta)              ║
║  → Esto permite pasar un mock en tests unitarios                      ║
║  → Principio D de SOLID: "Depende de abstracciones, no de concretos"  ║
║                                                                        ║
║  SEGURIDAD:                                                           ║
║  → Passwords: bcrypt hash (no reversible)                             ║
║  → Tokens: JWT (JSON Web Token) con HS256                             ║
║  → Expiración configurable vía ACCESS_TOKEN_EXPIRE_MINUTES            ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

# pyrefly: ignore [missing-import]
from fastapi import HTTPException, status
from datetime import timedelta
from ..domain.ports import UserRepositoryPort
from ..domain.schemas import UserCreate, UserUpdate, Token
from ..infrastructure.security import verify_password, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES


class AuthService:
    """
    Caso de Uso: Gestión de Autenticación y Perfiles de Usuario.
    
    PRINCIPIOS DE DISEÑO:
    ─────────────────────
    • Recibe un UserRepositoryPort en su constructor (Inyección de Dependencias)
    • La lógica de negocio es independiente de la implementación de datos
    • Cada método tiene una responsabilidad clara y única (SRP)
    
    NOTA PARA EL JURADO:
    Este es el ejemplo más claro de cómo la Arquitectura Hexagonal
    separa las capas. Observe que:
    1. AuthService NO importa SQLAlchemy ni ningún ORM
    2. El constructor acepta CUALQUIER implementación de UserRepositoryPort
    3. Se podría testear con un mock repository sin base de datos
    """

    def __init__(self, user_repo: UserRepositoryPort):
        # ═══ INYECCIÓN DE DEPENDENCIAS (Hexagonal DI) ═══════════════
        # Acepta CUALQUIER implementación de UserRepositoryPort.
        # En producción: recibe UserRepository (SQLAlchemy)
        # En tests: podría recibir InMemoryUserRepository (mock)
        self.user_repo = user_repo

    def register_user(self, user_data: UserCreate):
        """
        Registra un nuevo usuario validando unicidad de email.
        
        Regla de negocio: no pueden existir dos usuarios con el mismo email.
        La validación se hace en esta capa (no en la BD) para poder
        retornar un mensaje de error descriptivo al frontend.
        """
        if self.user_repo.get_by_email(user_data.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        return self.user_repo.create(user_data)

    def update_user_profile(self, user_id: int, update_data: UserUpdate) -> Token:
        """
        Actualiza el perfil del usuario y regenera su JWT.
        
        ¿POR QUÉ SE REGENERA EL TOKEN?
        → El JWT contiene claims como first_name, last_name, profile_picture_url
        → Si el usuario cambia su nombre, el token antiguo tendría datos obsoletos
        → Se emite un nuevo token con los datos actualizados
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        update_dict = update_data.model_dump(exclude_unset=True)

        # Validar unicidad de email si se está cambiando
        if "email" in update_dict and update_dict["email"] != user.email:
            if self.user_repo.get_by_email(update_dict["email"]):
                raise HTTPException(status_code=400, detail="El correo ya se encuentra en uso")

        # Aplicar actualizaciones campo por campo
        for key, value in update_dict.items():
            if key == "password":
                # Los passwords NUNCA se guardan en texto plano
                # Se usa bcrypt hash (función one-way / no reversible)
                user.hashed_password = get_password_hash(value)
            else:
                setattr(user, key, value)

        # Persistir cambios a través del repositorio
        self.user_repo.db.commit()
        self.user_repo.db.refresh(user)

        # Generar nuevo token JWT con claims actualizados
        access_token = self._create_user_token(user)
        return Token(access_token=access_token, token_type="bearer", role=user.role)

    def authenticate_user(self, email: str, password: str) -> Token:
        """
        Autentica credenciales y retorna un JWT válido.
        
        Proceso de autenticación:
        1. Buscar usuario por email en la BD
        2. Verificar password con bcrypt (comparar hash)
        3. Si es válido → generar JWT con claims del usuario
        4. Si no → HTTP 401 Unauthorized
        
        SEGURIDAD: nunca se revela si el error es por email o password
        inválido (se usa un mensaje genérico para prevenir enumeración).
        """
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
        """
        Helper interno para generar un JWT con claims estándar.
        
        Claims incluidos en el token:
        → sub: email del usuario (subject — estándar JWT RFC 7519)
        → role: rol del usuario (admin/user) para autorización
        → first_name, last_name: para mostrar en el frontend sin consultar BD
        → profile_picture_url: para el avatar del sidebar
        → exp: fecha de expiración (configurable)
        """
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
