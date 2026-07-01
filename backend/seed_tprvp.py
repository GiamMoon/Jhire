import os
import sys
# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.infrastructure.models import Order, Invoice
from datetime import datetime, timedelta
import random

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jhire_user:jhire_password@db:5432/jhire_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Delete existing dummy invoices in that range
start_date = datetime(2026, 3, 17)
end_date = datetime(2026, 5, 15, 23, 59, 59)
db.query(Invoice).filter(Invoice.issue_date >= start_date, Invoice.issue_date <= end_date).delete()
db.commit()

# Create invoices for our 60 dummy orders
orders = db.query(Order).filter(Order.created_at >= start_date, Order.created_at <= end_date).order_by(Order.created_at).all()

for idx, order in enumerate(orders):
    d = order.created_at
    # Para que NO se vea como una copia del indicador TPRCP, la venta (Invoice)
    # se realizará unas horas más tarde que la cotización (Order).
    random_offset_seconds = random.randint(3600, 18000) # 1 a 5 horas despues
    issue_date_venta = d + timedelta(seconds=random_offset_seconds)
    
    # Pre-test (17 Mar - 15 Abr)
    if d >= datetime(2026, 3, 17) and d <= datetime(2026, 4, 15, 23, 59, 59):
        # max 2 min 30s (150s), min 46s
        t_seconds = random.randint(46, 150)
    # Post-test (16 Abr - 15 May)
    else:
        # max 45s
        t_seconds = random.randint(10, 45)
        
    inv = Invoice(
        order_id=order.id,
        invoice_number=f"F001-{1000 + idx}",
        client_ruc_dni="20123456789",
        client_name="ESCOBILLAS INDUSTRIALES JHIRE",
        subtotal=order.total_price / 1.18,
        igv=order.total_price - (order.total_price / 1.18),
        total=order.total_price,
        issue_date=issue_date_venta,
        sunat_status="Emitida",
        registration_time_seconds=t_seconds
    )
    db.add(inv)

db.commit()
db.close()
print("Data de ventas (TPRVP) re-inyectada con nuevas horas y tiempos ajustados.")
