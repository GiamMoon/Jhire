import os
import sys
# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.infrastructure.models import Order, User
from datetime import datetime, timedelta
import random

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jhire_user:jhire_password@db:5432/jhire_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Delete existing dummy orders between March 17 and May 15
start_date = datetime(2026, 3, 17)
end_date = datetime(2026, 5, 15, 23, 59, 59)
db.query(Order).filter(Order.created_at >= start_date, Order.created_at <= end_date).delete()

# get a user id
user = db.query(User).first()
if not user:
    user = User(email="test@test.com", hashed_password="pw", role="admin")
    db.add(user)
    db.commit()
    db.refresh(user)
user_id = user.id

# Pre-Test
for i in range(30):
    current_date = datetime(2026, 3, 17, 12, 0, 0) + timedelta(days=i)
    total_venta = round(random.uniform(30.0, 99.0), 2)
    order = Order(user_id=user_id, status="Completado", total_price=total_venta, created_at=current_date)
    db.add(order)

# Post-Test
for i in range(30):
    current_date = datetime(2026, 4, 16, 12, 0, 0) + timedelta(days=i)
    total_venta = round(random.uniform(110.0, 299.0), 2)
    order = Order(user_id=user_id, status="Completado", total_price=total_venta, created_at=current_date)
    db.add(order)

db.commit()
db.close()
print("Data seeded successfully!")
