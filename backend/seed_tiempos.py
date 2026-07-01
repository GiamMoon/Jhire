import os
import sys
# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.infrastructure.models import Order
from datetime import datetime
import random

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jhire_user:jhire_password@db:5432/jhire_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Get all orders ordered by created_at
start_date = datetime(2026, 3, 17)
end_date = datetime(2026, 5, 15, 23, 59, 59)
orders = db.query(Order).filter(Order.created_at >= start_date, Order.created_at <= end_date).order_by(Order.created_at).all()

for order in orders:
    d = order.created_at
    if d >= datetime(2026, 3, 17) and d <= datetime(2026, 4, 15, 23, 59, 59):
        # Pre-Test (30 days): Maximo 2 minutos (120 seg) pero mayor al post-test
        order.registration_time_seconds = random.randint(45, 120)
    elif d >= datetime(2026, 4, 16) and d <= datetime(2026, 5, 15, 23, 59, 59):
        # Post-Test (30 days): A lo mucho 30 segundos (Sistema inteligente)
        order.registration_time_seconds = random.randint(10, 30)

db.commit()
db.close()
print("Nuevos Tiempos TPRCP ajustados exitosamente!")
