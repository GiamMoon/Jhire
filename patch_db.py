import sqlite3
import os

db_path = r"backend\jhire.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Check if column exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    if "profile_picture_url" not in columns:
        print("Adding profile_picture_url to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN profile_picture_url VARCHAR;")
        conn.commit()
    else:
        print("Column profile_picture_url already exists.")
    conn.close()
    print("Database patching completed via SQLite.")
else:
    print(f"Database jhire.db not found at {db_path}. Assuming PostgreSQL or different local path. Not patching manually, please verify.")
