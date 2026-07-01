from app.infrastructure.security import get_password_hash
from app.infrastructure.database import SessionLocal
from app.infrastructure.models import User

db = SessionLocal()
admin = db.query(User).filter(User.email == "giampier").first()
if admin:
    print("Found admin:", admin.email)
    print("Old hash:", admin.hashed_password)
    admin.hashed_password = get_password_hash("123")
    db.commit()
    print("Password updated to 123 successfully.")
else:
    print("Admin not found.")
