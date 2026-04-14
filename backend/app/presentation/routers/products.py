from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ...infrastructure.database import get_db
from ...infrastructure.models import Product
from ...domain.schemas import ProductResponse

router = APIRouter()

@router.get("", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
