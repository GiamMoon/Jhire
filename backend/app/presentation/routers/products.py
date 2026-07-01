from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ...infrastructure.database import get_db
from ...infrastructure.models import Product

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
import numpy as np

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price_soles: float
    image_url: Optional[str] = None
    stock: int
    category: Optional[str] = None

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price_soles: float
    image_url: Optional[str] = None
    stock: int = 0
    category: Optional[str] = "general"
    registration_time_seconds: Optional[int] = 0


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_soles: Optional[float] = None
    image_url: Optional[str] = None
    stock: Optional[int] = None
    category: Optional[str] = None

class PredictRequest(BaseModel):
    name: str

class PredictResponse(BaseModel):
    predicted_category: str
    predicted_price: float


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


@router.post("", response_model=ProductResponse)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    product = Product(
        name=data.name,
        description=data.description,
        price_soles=data.price_soles,
        image_url=data.image_url,
        stock=data.stock,
        category=data.category,
        registration_time_seconds=data.registration_time_seconds,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    db.delete(product)
    db.commit()
    return {"message": f"Producto '{product.name}' eliminado correctamente"}

@router.get("/tprp/reporte", response_model=None)
def get_tprp(db: Session = Depends(get_db)):
    """
    Obtiene los datos para el indicador TPRP (Tiempo Promedio en el Registro de Productos).
    """
    products = db.query(Product).filter(Product.registration_time_seconds > 0).order_by(Product.created_at).all()
    
    results = []
    total_time = 0
    
    for idx, p in enumerate(products, start=1):
        tf = p.created_at
        if not tf:
            from datetime import datetime
            tf = datetime.utcnow()
        from datetime import timedelta
        ti = tf - timedelta(seconds=p.registration_time_seconds)
        
        m, s = divmod(p.registration_time_seconds, 60)
        h, m = divmod(m, 60)
        trp_str = f"{h:02d}:{m:02d}:{s:02d}"
        
        results.append({
            "item": idx,
            "fecha": tf.strftime("%d/%m/%Y"),
            "tiempo_inicial": ti.strftime("%H:%M:%S"),
            "tiempo_final": tf.strftime("%H:%M:%S"),
            "tiempo_registro": trp_str,
            "trp_seconds": p.registration_time_seconds,
            "product_name": p.name
        })
        total_time += p.registration_time_seconds
        
    avg_seconds = total_time / len(products) if products else 0
    avg_m, avg_s = divmod(int(avg_seconds), 60)
    avg_h, avg_m = divmod(avg_m, 60)
    avg_str = f"{avg_h:02d}:{avg_m:02d}:{avg_s:02d}"
    
    return {
        "data": results,
        "promedio_str": avg_str,
        "promedio_seconds": avg_seconds
    }

@router.post("/predict-attributes", response_model=PredictResponse)
def predict_attributes(data: PredictRequest, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    # Si hay muy pocos datos, devolver valores por defecto
    if len(products) < 2:
        return PredictResponse(predicted_category="general", predicted_price=0.0)

    names = [p.name for p in products]
    categories = [p.category or "general" for p in products]
    prices = [p.price_soles for p in products]

    try:
        # PNL: Convertir nombres a vectores de frecuencia de palabras
        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(names)
        
        # Clasificador para Categoría
        clf = RandomForestClassifier(n_estimators=20, random_state=42)
        clf.fit(X, categories)
        
        # Regresor para Precio
        reg = RandomForestRegressor(n_estimators=20, random_state=42)
        reg.fit(X, prices)
        
        # Predicción sobre el nuevo nombre
        X_new = vectorizer.transform([data.name])
        
        # Fallback si el vectorizador ignora la palabra (ej: palabra nueva)
        if X_new.nnz == 0:
            return PredictResponse(predicted_category="general", predicted_price=round(float(np.mean(prices)), 2))
        
        pred_cat = clf.predict(X_new)[0]
        pred_price = reg.predict(X_new)[0]
        
        return PredictResponse(
            predicted_category=str(pred_cat),
            predicted_price=round(float(pred_price), 2)
        )
    except Exception as e:
        print("ML Error:", e)
        return PredictResponse(predicted_category="general", predicted_price=0.0)
