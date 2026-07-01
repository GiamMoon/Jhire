import os
from sqlalchemy import text
from app.infrastructure.database import engine

def seed_db():
    img_esc_1 = "assets/images/escobilla_1.png"
    img_esc_mini = "assets/images/escobilla_mini.png"
    img_rod_1 = "assets/images/rodillo_1.png"
    img_rod_heavy = "assets/images/rodillo_heavy.png"

    products = [
        ("Escobilla de Acero Circular 400mm", "Escobilla industrial para pulido pesado, cerdas de acero al carbono.", 120.50, img_esc_1, 50, "escobillas"),
        ("Escobilla de Acero Circular 200mm", "Escobilla industrial para pulido medio, cerdas de acero.", 85.00, img_esc_1, 80, "escobillas"),
        ("Escobilla de Copa Trenzada 4 pulg", "Remoción agresiva de óxido y pintura.", 45.90, img_esc_mini, 120, "escobillas"),
        ("Rodillo de Nylon Industrial Pro-X 300mm", "Rodillo de nylon de alta densidad para limpieza de fajas transportadoras.", 250.00, img_rod_heavy, 30, "rodillos"),
        ("Rodillo de Nylon Industrial 150mm", "Rodillo compacto para uso en áreas estrechas.", 145.00, img_rod_1, 45, "rodillos"),
        ("Disco Cepillo Limpiador de Pisos 20 pulg", "Cepillo para restregadora automática de pisos.", 180.00, img_esc_1, 25, "limpieza"),
        ("Rodillo de Microfibra Epóxica 9 pulg", "Ideal para aplicación de recubrimientos epóxicos industriales.", 35.50, img_rod_1, 200, "rodillos"),
        ("Rodillo de Microfibra Epóxica 18 pulg", "Cobertura rápida en áreas grandes.", 65.00, img_rod_heavy, 150, "rodillos"),
        ("Escobilla Manual de Acero Inoxidable", "Para limpieza detallada, no contamina piezas de acero inoxidable.", 18.50, img_esc_mini, 300, "escobillas"),
        ("Brocha Industrial de Cerdas Naturales 4 pulg", "Para aplicación de solventes y resinas.", 22.00, img_esc_mini, 180, "brochas")
    ]

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            conn.execute(text("TRUNCATE TABLE products CASCADE"))
            for p in products:
                conn.execute(text("""
                    INSERT INTO products (name, description, price_soles, image_url, stock, category, registration_time_seconds)
                    VALUES (:name, :desc, :price, :img, :stock, :cat, :time)
                """), {
                    "name": p[0],
                    "desc": p[1],
                    "price": p[2],
                    "img": p[3],
                    "stock": p[4],
                    "cat": p[5],
                    "time": 25 # mock registration time
                })
            trans.commit()
            print("DB Seeded Successfully!")
        except Exception as e:
            trans.rollback()
            print(f"Error seeding DB: {e}")

if __name__ == "__main__":
    seed_db()
