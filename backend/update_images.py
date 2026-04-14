import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.infrastructure.database import SessionLocal
from app.infrastructure.models import Product

def update_images():
    db = SessionLocal()
    products = db.query(Product).all()
    # Vary the images dynamically using realistic industrial tools placeholders
    for i, p in enumerate(products):
        # We leave the first few with their original assets if they look like the defaults
        if i % 3 == 0:
            p.image_url = "/assets/images/escobilla_1.png"
        elif i % 3 == 1:
            p.image_url = "/assets/images/rodillo_1.png"
        else:
            # Use random varied placeholders that have different colors
            p.image_url = f"https://picsum.photos/seed/jhire_{p.id}/400/400?grayscale&blur=2"
            
    db.commit()
    db.close()
    print("Las imágenes han sido actualizadas y variadas exitosamente en la BD.")

if __name__ == "__main__":
    update_images()
