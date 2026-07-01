import os
from sqlalchemy import text
from app.infrastructure.database import engine

def alter_table():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE orders ADD COLUMN registration_time_seconds INTEGER DEFAULT 0;"))
            print("Added registration_time_seconds to orders")
        except Exception as e:
            print("Column registration_time_seconds might already exist in orders:", e)
        conn.commit()

if __name__ == "__main__":
    alter_table()
