import os
import sys
from sqlalchemy import text
from app.infrastructure.database import engine

def alter_table():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN registration_time_seconds INTEGER DEFAULT 0;"))
            print("Added registration_time_seconds")
        except Exception as e:
            print("Column registration_time_seconds might already exist:", e)
            
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))
            print("Added created_at")
        except Exception as e:
            print("Column created_at might already exist:", e)
            
        conn.commit()

if __name__ == "__main__":
    alter_table()
