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

# We only need to UPDATE the processing_time_seconds of existing POST-TEST invoices
# The user wants realistic times for the Post-test, not just 1-5 seconds.
# We will set them to 2 to 6 minutes (120 to 360 seconds) per invoice.

post_test_start = datetime(2026, 4, 16)
post_test_end = datetime(2026, 5, 15, 23, 59, 59)

post_test_invoices = db.query(Invoice).filter(
    Invoice.issue_date >= post_test_start,
    Invoice.issue_date <= post_test_end,
    Invoice.processing_time_seconds > 0
).all()

count = 0
for inv in post_test_invoices:
    # 2 a 6 minutos por factura, realista para un proceso de revisión y click en "Emitir SUNAT"
    inv.processing_time_seconds = random.randint(120, 360)
    count += 1

db.commit()
db.close()
print(f"Se actualizaron {count} facturas del Post-Test con tiempos más realistas (2-6 minutos).")
