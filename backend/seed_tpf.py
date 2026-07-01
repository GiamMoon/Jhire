import os
import sys
# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.infrastructure.models import Order, Invoice, User
from datetime import datetime, timedelta
import random

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jhire_user:jhire_password@db:5432/jhire_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# 1. Alter Table
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS processing_time_seconds INTEGER DEFAULT 0;"))
    print("Columna processing_time_seconds agregada a invoices.")
except Exception as e:
    print(f"Error al alterar tabla: {e}")

# get a user id
user = db.query(User).first()
if not user:
    user = User(email="admin_tpf@test.com", hashed_password="pw", role="admin")
    db.add(user)
    db.commit()
    db.refresh(user)
user_id = user.id

# We want 30 days of Pre-test and 30 days of Post-test
# But we already have 1 order/invoice per day. We will ADD 4 to 14 more per day
# so the total is 5 to 15 per day.
# Actually, let's just generate the extra ones.

def seed_extra_invoices(start_d, end_d, pre_test=True):
    current_date = start_d
    while current_date <= end_d:
        # Generar entre 4 y 14 extras (para sumar 5 a 15 con el que ya existe)
        extras = random.randint(4, 14)
        for i in range(extras):
            # Order
            order = Order(
                user_id=user_id,
                status="Completado",
                total_price=round(random.uniform(20.0, 300.0), 2),
                created_at=current_date + timedelta(hours=random.randint(1, 10)),
                registration_time_seconds=0 # Not used for this metric
            )
            db.add(order)
            db.flush() # Para obtener el ID

            # Invoice
            if pre_test:
                # 15 a 45 minutos (900 a 2700 seg)
                t_proc = random.randint(900, 2700)
            else:
                # 1 a 5 segundos
                t_proc = random.randint(1, 5)

            inv = Invoice(
                order_id=order.id,
                invoice_number=f"F001-EXTRA-{current_date.strftime('%Y%m%d')}-{i}",
                client_ruc_dni="20123456789",
                client_name="ESCOBILLAS INDUSTRIALES JHIRE",
                subtotal=order.total_price / 1.18,
                igv=order.total_price - (order.total_price / 1.18),
                total=order.total_price,
                issue_date=order.created_at + timedelta(minutes=random.randint(10, 60)),
                sunat_status="Emitida",
                registration_time_seconds=0, # Not used
                processing_time_seconds=t_proc
            )
            db.add(inv)
        current_date += timedelta(days=1)

# Pre-test
seed_extra_invoices(datetime(2026, 3, 17), datetime(2026, 4, 15), pre_test=True)
# Post-test
seed_extra_invoices(datetime(2026, 4, 16), datetime(2026, 5, 15), pre_test=False)

# Update the EXISTING 60 invoices processing time too!
existing_invoices = db.query(Invoice).filter(
    Invoice.invoice_number.not_like("%EXTRA%")
).all()

for inv in existing_invoices:
    d = inv.issue_date
    if d >= datetime(2026, 3, 17) and d <= datetime(2026, 4, 15, 23, 59, 59):
        inv.processing_time_seconds = random.randint(900, 2700)
    elif d >= datetime(2026, 4, 16) and d <= datetime(2026, 5, 15, 23, 59, 59):
        inv.processing_time_seconds = random.randint(1, 5)

db.commit()
db.close()
print("Data masiva de facturación (TPF) inyectada exitosamente.")
