from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from ...infrastructure.database import get_db
from ...domain.schemas import OrderCreate, OrderResponse, OrderStatusUpdate
from ...infrastructure.models import Order, OrderItem, Product, User
from ...infrastructure.security import get_current_user
from ...infrastructure.email import send_async_email
from ...infrastructure.websocket_manager import manager
import json

router = APIRouter()

async def notify_dashboard_refresh():
    await manager.broadcast(json.dumps({"event": "refresh_dashboard"}))

@router.post("/", response_model=OrderResponse)
def create_order(order_data: OrderCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not order_data.items:
        raise HTTPException(status_code=400, detail="El carrito no puede estar vacío")
    
    total_price = 0.0
    new_order = Order(user_id=current_user.id, status="En Proceso")
    db.add(new_order)
    db.flush() # Para obetener new_order.id
    
    for item in order_data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Producto ID {item.product_id} no encontrado")
        
        # Calculate amount
        line_total = product.price_soles * item.quantity
        total_price += line_total
        
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=product.id,
            quantity=item.quantity,
            unit_price=product.price_soles
        )
        db.add(order_item)
    
    new_order.total_price = total_price
    
    # Anomaly Detection
    from sqlalchemy.sql import func
    avg_spent = db.query(func.avg(Order.total_price)).filter(Order.user_id == current_user.id, Order.status != "Cancelado").scalar()
    
    if avg_spent and avg_spent > 0 and total_price > (avg_spent * 3):
        new_order.status = "Anomalía / Revisión"
        
    db.commit()
    db.refresh(new_order)
    
    # Send order confirmation email async
    content = f"Estimado/a cliente,\n\nSu orden #ORD-{new_order.id} ha sido recibida con éxito. El total asciende a S/ {new_order.total_price}. En breve procesaremos su solicitud."
    send_async_email(
        background_tasks=background_tasks, 
        to_email=current_user.email, 
        subject=f"Confirmación de Orden JHIRE (#ORD-{new_order.id})", 
        content=content
    )
    
    background_tasks.add_task(notify_dashboard_refresh)
    
    return new_order

@router.get("/me", response_model=List[OrderResponse])
def get_my_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()
    # Check if any "En Proceso" order has expired (> 72 hours)
    for order in orders:
        if order.status == "En Proceso":
            elapsed = (datetime.utcnow() - order.created_at).total_seconds()
            if elapsed > 72 * 3600:
                order.status = "Cancelado"
                db.commit()
    return orders

@router.get("/admin", response_model=List[OrderResponse])
def get_admin_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    
    orders = db.query(Order).filter(Order.status == "En Proceso").order_by(Order.created_at.desc()).all()
    # Expire globally if requested
    for order in orders:
        if order.status == "En Proceso":
            elapsed = (datetime.utcnow() - order.created_at).total_seconds()
            if elapsed > 72 * 3600:
                order.status = "Cancelado"
                db.commit()
    
    # Refetch pending orders after possible cancellations
    return db.query(Order).filter(Order.status == "En Proceso").order_by(Order.created_at.desc()).all()

@router.get("/admin/all", response_model=List[OrderResponse])
def get_all_admin_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Returns ALL orders (Approved, Rejected, Pending, Cancelled) to have a historical view per user."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
        
    return db.query(Order).order_by(Order.user_id.asc(), Order.created_at.desc()).all()

@router.put("/{order_id}/status", response_model=OrderResponse)
def update_order_status(order_id: int, status_update: OrderStatusUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
        
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
        
    order.status = status_update.status
    db.commit()
    db.refresh(order)
    
    # Send status update email async
    status_content = f"Estimado/a cliente,\n\nSu orden #ORD-{order.id} ha cambiado de estado a: {order.status}.\nGracias por confiar en JHIRE 2026."
    send_async_email(
        background_tasks=background_tasks, 
        to_email=order.user.email, 
        subject=f"Actualización de Orden JHIRE (#ORD-{order.id})", 
        content=status_content
    )
    
    background_tasks.add_task(notify_dashboard_refresh)
    
    return order
