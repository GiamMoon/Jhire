from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from ...infrastructure.database import get_db
from ...infrastructure.models import Product, InventoryMovement, Supplier
from ...domain.schemas import InventoryMovementCreate

router = APIRouter()

@router.get("/")
def get_inventory_summary(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    finished = sum(p.stock for p in products)
    low_stock = sum(1 for p in products if p.stock < 20)
    
    movements_count = db.query(func.count(InventoryMovement.id)).scalar() or 0
    
    suppliers = db.query(Supplier).all()
    suppliers_list = [{"name": s.name, "lead_time": f"{s.lead_time_days} Days"} for s in suppliers]
    
    recent_movements = db.query(InventoryMovement).order_by(InventoryMovement.date.desc()).limit(10).all()
    
    movs = []
    for m in recent_movements:
        prod = db.query(Product).filter(Product.id == m.product_id).first()
        movs.append({"sku": f"JHIRE-{m.product_id}", "desc": f"[{m.type}] {prod.name if prod else 'Unknown'} - Qty: {m.quantity}"})

    return {
        "raw_materials": int(finished * 0.4), # Mock calculation for raw material based on total stock
        "finished_products": finished,
        "low_stock_items": low_stock,
        "total_movements_week": movements_count,
        "suppliers": suppliers_list,
        "movements": movs,
        "ai_suggestion": "Basado en el stock en tiempo real, se requiere abastecimiento urgente para los ítems con escasez." if low_stock > 0 else "Los niveles de inventario se encuentran estables y dentro de los márgenes de seguridad."
    }

@router.post("/movement")
def register_movement(movement: InventoryMovementCreate, db: Session = Depends(get_db)):
    prod = db.query(Product).filter(Product.id == movement.product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Producto no encontrado en inventario")
        
    if movement.type == "Entrada":
        prod.stock += movement.quantity
    else:
        if prod.stock < movement.quantity:
            raise HTTPException(status_code=400, detail="Stock Insuficiente: No se pueden retirar más unidades de las existentes.")
        prod.stock -= movement.quantity
    
    new_mov = InventoryMovement(**movement.dict())
    db.add(new_mov)
    db.commit()
    return {"message": "Movimiento registrado"}
