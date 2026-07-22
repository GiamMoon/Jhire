"""
JHIRE 2026 — Domain Ports (Arquitectura Hexagonal)
=====================================================
TESIS: Sistema Web para la Gestión Comercial de la Empresa JHIRE

╔══════════════════════════════════════════════════════════════════════════╗
║  ARQUITECTURA HEXAGONAL — PUERTOS DEL DOMINIO (Domain Ports)           ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  ¿QUÉ SON LOS PUERTOS?                                               ║
║  ─────────────────────                                                ║
║  Los puertos son INTERFACES ABSTRACTAS (contratos) que definen        ║
║  las operaciones que el dominio NECESITA, sin especificar CÓMO        ║
║  se implementan. Son el equivalente a "interfaces" en Java o          ║
║  "protocols" en Swift.                                                ║
║                                                                        ║
║  ¿POR QUÉ USAMOS PUERTOS?                                            ║
║  ─────────────────────────                                            ║
║  1. INVERSIÓN DE DEPENDENCIA (Principio D de SOLID):                  ║
║     → El dominio NO depende de SQLAlchemy, PostgreSQL, ni nada        ║
║       específico de infraestructura.                                  ║
║     → La infraestructura implementa los puertos del dominio.          ║
║                                                                        ║
║  2. TESTABILIDAD:                                                     ║
║     → Podemos crear mocks/stubs de estos puertos para unit tests      ║
║       sin necesitar una base de datos real.                           ║
║                                                                        ║
║  3. INTERCAMBIABILIDAD:                                               ║
║     → Se puede cambiar de SQLite a PostgreSQL, MongoDB, o incluso     ║
║       a un servicio externo (API REST), sin tocar el dominio.         ║
║     → Solo se cambia la implementación del adaptador.                 ║
║                                                                        ║
║  DIAGRAMA DE LA ARQUITECTURA:                                         ║
║  ┌─────────────────────────────────────────────────────────────┐      ║
║  │                    PRESENTACIÓN (Routers)                   │      ║
║  │              FastAPI endpoints, HTTP, WebSocket              │      ║
║  └───────────────────────┬─────────────────────────────────────┘      ║
║                          │                                            ║
║                          ▼                                            ║
║  ┌─────────────────────────────────────────────────────────────┐      ║
║  │               CASOS DE USO (Use Cases)                      │      ║
║  │        AuthService, RecommendationService                    │      ║
║  │        Contienen la lógica de negocio de la aplicación       │      ║
║  └───────────────────────┬─────────────────────────────────────┘      ║
║                          │ depende de ↓                               ║
║  ┌─────────────────────────────────────────────────────────────┐      ║
║  │          ★ DOMINIO (Ports + Schemas) ★ ← ESTE ARCHIVO       │      ║
║  │      Interfaces abstractas + Modelos de datos Pydantic       │      ║
║  │      NO depende de NADA externo — es el NÚCLEO               │      ║
║  └───────────────────────┬─────────────────────────────────────┘      ║
║                          │ implementado por ↓                         ║
║  ┌─────────────────────────────────────────────────────────────┐      ║
║  │              INFRAESTRUCTURA (Adaptadores)                  │      ║
║  │        SQLAlchemy Models, Repositories, Email SMTP           │      ║
║  │        Implementación concreta de los puertos                │      ║
║  └─────────────────────────────────────────────────────────────┘      ║
║                                                                        ║
║  Referencia: Cockburn, A. (2005). "Hexagonal Architecture"            ║
║  También conocida como "Ports and Adapters Pattern"                   ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════
# PUERTO: Repositorio de Usuarios
# ═══════════════════════════════════════════════════════════════════════
# Define las operaciones CRUD para usuarios que el dominio necesita.
# La implementación concreta está en:
#   infrastructure/repositories/user_repository.py → UserRepository

class UserRepositoryPort(ABC):
    """
    Puerto (interfaz abstracta) para acceso a datos de Usuario.
    
    Implementado por: UserRepository (infrastructure/repositories/)
    
    ¿Por qué ABC (Abstract Base Class)?
    → Python no tiene interfaces nativas como Java.
    → ABC + @abstractmethod obliga a las clases hijas a implementar
      todos los métodos, generando un error si se olvidan.
    → Esto garantiza que cualquier adaptador que se cree cumplirá
      el contrato completo.
    """

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


# ═══════════════════════════════════════════════════════════════════════
# PUERTO: Repositorio de Productos
# ═══════════════════════════════════════════════════════════════════════

class ProductRepositoryPort(ABC):
    """
    Puerto para acceso a datos de Productos.
    
    Implementado por: ProductRepository (infrastructure/repositories/)
    """

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


# ═══════════════════════════════════════════════════════════════════════
# PUERTO: Repositorio de Órdenes
# ═══════════════════════════════════════════════════════════════════════

class OrderRepositoryPort(ABC):
    """
    Puerto para acceso a datos de Órdenes de compra.
    
    Implementado por: OrderRepository (infrastructure/repositories/)
    """

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


# ═══════════════════════════════════════════════════════════════════════
# PUERTO: Repositorio de Facturas
# ═══════════════════════════════════════════════════════════════════════

class InvoiceRepositoryPort(ABC):
    """
    Puerto para acceso a datos de Facturación Electrónica.
    
    Las facturas siguen el estándar UBL 2.1 de SUNAT Perú.
    """

    @abstractmethod
    def get_by_id(self, invoice_id: int):
        ...

    @abstractmethod
    def create(self, order_id: int, client_ruc_dni: str, client_name: str) -> object:
        ...

    @abstractmethod
    def get_next_invoice_number(self) -> str:
        ...


# ═══════════════════════════════════════════════════════════════════════
# PUERTO: Repositorio de Vistas de Productos (para IA de Recomendación)
# ═══════════════════════════════════════════════════════════════════════

class ProductViewRepositoryPort(ABC):
    """
    Puerto para el tracking de vistas de productos.
    
    Este puerto es FUNDAMENTAL para el motor de recomendación IA:
    → track_view: registra cada vez que un usuario ve un producto
    → get_user_views: obtiene el historial de navegación del usuario
    → get_trending: detecta productos trending globalmente
    
    Estos datos alimentan el algoritmo de scoring en
    use_cases/recommendation_service.py
    """

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


# ═══════════════════════════════════════════════════════════════════════
# PUERTO: Repositorio de CRM (Customer Relationship Management)
# ═══════════════════════════════════════════════════════════════════════

class CRMRepositoryPort(ABC):
    """
    Puerto para interacciones del CRM.
    
    Registra todos los contactos con clientes (emails, WhatsApp,
    llamadas, visitas) para análisis de segmentación y retención.
    """

    @abstractmethod
    def log_interaction(self, user_id: int, interaction_type: str, notes: str):
        ...

    @abstractmethod
    def get_interactions(self, user_id: int) -> List:
        ...


# ═══════════════════════════════════════════════════════════════════════
# PUERTO: Servicio de Email (Infraestructura Externa)
# ═══════════════════════════════════════════════════════════════════════

class EmailServicePort(ABC):
    """
    Puerto para envío de correos electrónicos.
    
    Desacopla el dominio de los detalles de SMTP/Gmail/SendGrid.
    La implementación concreta puede:
    → Usar SMTP directo (Gmail) en desarrollo
    → Usar SendGrid/AWS SES en producción
    → Usar un mock en testing (no envía emails reales)
    
    Todo esto SIN cambiar el código del dominio.
    """

    @abstractmethod
    def send_email(self, to_email: str, subject: str, content: str):
        """Send an email asynchronously."""
        ...
