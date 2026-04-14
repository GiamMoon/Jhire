from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .infrastructure.database import engine, Base, SessionLocal
from .infrastructure.models import User, Product
from .infrastructure.security import get_password_hash
from .presentation.routers import auth

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="JHIRE 2025 API")

@app.on_event("startup")
def seed_admin_user_and_products():
    db = SessionLocal()
    try:
        admin_email = "giampier" # The username required: giampier
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            hashed_pwd = get_password_hash("123")
            new_admin = User(email=admin_email, hashed_password=hashed_pwd, role="admin", first_name="Giampier", last_name="Admin")
            db.add(new_admin)
            db.commit()
            
        # Seed Products if empty
        if db.query(Product).count() == 0:
            products_data = [
                {"name": "Escobilla Industrial de Nylon Negro", "description": "Cepillo de alta resistencia, cerdas de nylon negro purificado, mango ergonómico. Uso industrial múltiple.", "price_soles": 45.50, "image_url": "assets/images/escobilla_1.png", "stock": 100},
                {"name": "Rodillo Cilíndrico de Nylon Negro", "description": "Rodillo rotativo denso de nylon para máquinas pulidoras. Larga durabilidad.", "price_soles": 120.00, "image_url": "assets/images/rodillo_1.png", "stock": 50},
                {"name": "Mini Escobilla de Detalle Nylon Negro", "description": "Ideal para limpieza de piezas mecánicas pequeñas. Cerdas rígidas.", "price_soles": 15.00, "image_url": "assets/images/escobilla_mini.png", "stock": 200},
                {"name": "Rodillo Pincel de Nylon Heavy-Duty", "description": "Rodillo ancho para aplicación uniforme, filamentos negros extra firmes.", "price_soles": 85.90, "image_url": "assets/images/rodillo_heavy.png", "stock": 35}
            ]
            for p in products_data:
                db.add(Product(**p))
            db.commit()
    finally:
        db.close()

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

from .presentation.routers import dashboard, sales, inventory, billing, products, chat, orders, contacts, crm, reports
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(sales.router, prefix="/api/sales", tags=["Sales"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["Inventory"])
app.include_router(billing.router, prefix="/api/billing", tags=["Billing"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(contacts.router, prefix="/api/contacto", tags=["Contacts"])
app.include_router(crm.router, prefix="/api/crm", tags=["CRM"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
# Mount Frontend Static Files if the folder exists (to serve the JHIRE screens)
import os
frontend_dir = "/frontend"
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
