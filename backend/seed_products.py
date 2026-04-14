import sys
import os
import random

# Ensure the app module can be found when run via command line
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.infrastructure.database import SessionLocal
from app.infrastructure.models import Product

def seed_db():
    db = SessionLocal()
    
    # Material prefixes
    materials = [
        "Nylon Negro", "Nylon Blanco", "Nylon Azul", "Nylon Rojo",
        "Cerdas de Acero Inoxidable", "Latón Corrugado", 
        "Nylon Heavy-Duty", "Feltro Industrial Prensado", 
        "Poliéster Abrasivo", "Fibra Natural de Tampico"
    ]
    # Object types
    types = [
        "Escobilla Cilíndrica de", "Rodillo Limpiador de", 
        "Cepillo Rotativo de", "Rodillo Purificador de", 
        "Pulidora Base de", "Banda Rotatoria de", 
        "Escobilla de Detalle de", "Sistema de Barrido de"
    ]
    # Sizes
    sizes = [
        "(Small 50cm)", "(Mediano 100cm)", "(Grande 150cm)", 
        "(Extra Grande 200cm)", "(Ø 100mm)", "(Ø 250mm)", "(Formato Customizado)"
    ]
    
    # Track inserted to avoid exact duplicates (just in case)
    inserted = 0
    
    while inserted < 50:
        mat = random.choice(materials)
        t = random.choice(types)
        size = random.choice(sizes)
        
        name = f"{t} {mat} {size}"
        
        # Fake images leveraging existing ones we saw in previous logs or using a generator
        # Since earlier logs showed /assets/images/escobilla_1.png and rodillo_1.png, we randomly pick from similar realistic mock links
        # If the user doesn't have 50 icons, using a high quality unsplash tech placeholder or just their localized images is safer.
        img = random.choice(["/assets/images/escobilla_1.png", "/assets/images/rodillo_1.png"])
        
        price = round(random.uniform(25.0, 450.0), 2)
        stock = random.randint(0, 1000) # Give it realistic industrial stocks
        
        desc = (
            f"Equipamiento de alta resistencia diseñado para el ámbito industrial pesado. "
            f"Elaborado con {mat.lower()}, ofrece una durabilidad excepcional, ideal para frotación, "
            f"limpieza profunda y mantenimiento en ambientes críticos de producción con alta fricción."
        )
        
        p = Product(
            name=name,
            description=desc,
            price_soles=price,
            stock=stock,
            image_url=img
        )
        db.add(p)
        inserted += 1
        
    try:
        db.commit()
        print("Base de datos operada: 50 productos de limpieza industrial de alta variedad inyectados existosamente.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Iniciando la siembra automatizada JHIRE...")
    seed_db()
