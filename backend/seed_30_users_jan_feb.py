"""
Seed script: Creates 30 new users and generates sales (Orders + OrderItems)
in January and February 2026. Does NOT touch any existing data.

Run from the backend directory:
    docker compose exec api python seed_30_users_jan_feb.py
    OR locally:
    python seed_30_users_jan_feb.py
"""

import os
import sys
import random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.infrastructure.models import User, Order, OrderItem, Product
from passlib.context import CryptContext

# ── Config ──────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://jhire_user:jhire_password@db:5432/jhire_db",
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DEFAULT_PASSWORD = pwd_context.hash("Jhire2026!")  # Same password for all seeded users

# ── 30 Realistic Peruvian names ─────────────────────────────────────────
NEW_USERS = [
    ("Carlos", "Quispe Mamani"),
    ("María", "Huamán Flores"),
    ("José", "Condori Apaza"),
    ("Ana", "Torres Villanueva"),
    ("Luis", "Chávez Ríos"),
    ("Rosa", "Mendoza Paredes"),
    ("Jorge", "Espinoza Cárdenas"),
    ("Patricia", "Vargas Taipe"),
    ("Pedro", "Ramos Gutiérrez"),
    ("Carmen", "Rojas Salazar"),
    ("Miguel", "Fernández Inga"),
    ("Lucía", "Castillo Herrera"),
    ("Roberto", "Palomino Vega"),
    ("Silvia", "Aquino Delgado"),
    ("Fernando", "Huanca Ccama"),
    ("Diana", "Zevallos Cruz"),
    ("Ricardo", "Mamani Puma"),
    ("Gabriela", "Soto Romero"),
    ("Andrés", "Ccorimanya León"),
    ("Teresa", "Ypanaqué Medina"),
    ("Diego", "Llanos Becerra"),
    ("Claudia", "Ticona Sullca"),
    ("Raúl", "Benítez Ochoa"),
    ("Verónica", "Arce Montoya"),
    ("Héctor", "Quispe Huayta"),
    ("Sandra", "Choque Larico"),
    ("Óscar", "Pillco Cusihuamán"),
    ("Elena", "Gamarra Vilca"),
    ("Julio", "Ccahuana Tito"),
    ("Mónica", "Yauri Huayhua"),
]

# ── Helper ──────────────────────────────────────────────────────────────
def random_date_in_month(year: int, month: int) -> datetime:
    """Return a random datetime within the given month."""
    if month == 12:
        max_day = 31
    else:
        next_month = datetime(year, month + 1, 1)
        max_day = (next_month - timedelta(days=1)).day
    day = random.randint(1, max_day)
    hour = random.randint(8, 18)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return datetime(year, month, day, hour, minute, second)


# ── Main ────────────────────────────────────────────────────────────────
def main():
    # Fetch existing products to assign to order items
    products = db.query(Product).all()
    if not products:
        print("⚠  No hay productos en la base de datos. Ejecuta seed_products.py primero.")
        db.close()
        return

    created_users = []

    # 1. Create 30 users
    for i, (first, last) in enumerate(NEW_USERS, start=1):
        email = f"{first.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')}.{last.split()[0].lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')}@jhire.pe"

        # Check if user already exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"  ⏭  Usuario ya existe: {email}")
            created_users.append(existing)
            continue

        user = User(
            first_name=first,
            last_name=last,
            phone=f"9{random.randint(10000000, 99999999)}",
            email=email,
            hashed_password=DEFAULT_PASSWORD,
            role="user",
            data_protection_consent=True,
        )
        db.add(user)
        db.flush()  # Get the ID
        created_users.append(user)
        print(f"  ✅ [{i:02d}/30] Usuario creado: {first} {last} ({email})")

    db.commit()
    print(f"\n{'='*60}")
    print(f"  Total usuarios nuevos listos: {len(created_users)}")
    print(f"{'='*60}\n")

    # 2. Generate sales (Orders + OrderItems) in January & February 2026
    total_orders = 0
    for user in created_users:
        # Each user gets between 5 and 15 orders spread across Jan-Feb
        num_orders = random.randint(5, 15)
        for _ in range(num_orders):
            month = random.choice([1, 2])  # January or February
            order_date = random_date_in_month(2026, month)

            # Create order
            order = Order(
                user_id=user.id,
                status="Completado",
                total_price=0.0,
                created_at=order_date,
                completed_at=order_date + timedelta(hours=random.randint(1, 48)),
                registration_time_seconds=random.randint(15, 120),
                sale_confirmation_seconds=random.randint(5, 60),
            )
            db.add(order)
            db.flush()

            # Add 1-4 items per order
            num_items = random.randint(1, 4)
            chosen_products = random.sample(products, min(num_items, len(products)))
            order_total = 0.0

            for prod in chosen_products:
                qty = random.randint(1, 10)
                unit_price = prod.price_soles
                item = OrderItem(
                    order_id=order.id,
                    product_id=prod.id,
                    quantity=qty,
                    unit_price=unit_price,
                )
                db.add(item)
                order_total += unit_price * qty

            order.total_price = round(order_total, 2)
            total_orders += 1

    db.commit()
    print(f"  📦 Total órdenes creadas (Enero-Febrero 2026): {total_orders}")
    print(f"  📊 Rango de fechas: 01/01/2026 – 28/02/2026")
    print(f"\n  ✅ ¡Seed completado exitosamente!")
    print(f"  ℹ  Password para todos los usuarios: Jhire2026!")
    print(f"  ℹ  Las fichas de registro (Mar-May) NO fueron modificadas.\n")

    db.close()


if __name__ == "__main__":
    main()
