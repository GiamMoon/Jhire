from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks # type: ignore
from sqlalchemy.orm import Session # type: ignore
from datetime import datetime
from typing import List
from ...infrastructure.database import get_db
from ...domain.schemas import OrderCreate, OrderResponse, OrderStatusUpdate
from ...infrastructure.models import Order, OrderItem, Product, User
from ...infrastructure.security import get_current_user
from ...infrastructure.email import send_async_email
from ...infrastructure.websocket_manager import manager
import json
from datetime import timedelta

router = APIRouter()


async def notify_dashboard_refresh():
    await manager.broadcast(json.dumps({"event": "refresh_dashboard"}))

@router.post("/", response_model=OrderResponse)
def create_order(order_data: OrderCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not order_data.items:
        raise HTTPException(status_code=400, detail="El carrito no puede estar vacío")
    
    total_price = 0.0
    new_order = Order(
        user_id=current_user.id, 
        status="En Proceso",
        registration_time_seconds=order_data.registration_time_seconds
    )
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
    
    from sqlalchemy.sql import func
    avg_spent = db.query(func.avg(Order.total_price)).filter(
        Order.user_id == current_user.id, 
        Order.status != "Cancelado",
        Order.id != new_order.id
    ).scalar()
    
    if avg_spent and avg_spent > 0 and total_price > (avg_spent * 3):
        new_order.status = "Anomalía / Revisión"
        
    db.commit()
    db.refresh(new_order)
    
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
    
    orders = db.query(Order).filter(Order.status.in_(["En Proceso", "Anomalía / Revisión"])).order_by(Order.created_at.desc()).all()
    for order in orders:
        if order.status == "En Proceso":
            elapsed = (datetime.utcnow() - order.created_at).total_seconds()
            if elapsed > 72 * 3600:
                order.status = "Cancelado"
                db.commit()
    
    return db.query(Order).filter(Order.status.in_(["En Proceso", "Anomalía / Revisión"])).order_by(Order.created_at.desc()).all()

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
    if status_update.status == "Completado":
        order.completed_at = datetime.utcnow()
        conf_seconds = status_update.sale_confirmation_seconds or 0
        if conf_seconds < 1:
            elapsed = int((order.completed_at - order.created_at).total_seconds())
            conf_seconds = min(max(1, elapsed), 300)
        order.sale_confirmation_seconds = conf_seconds
    db.commit()
    db.refresh(order)
    
    status_content = f"Estimado/a cliente,\n\nSu orden #ORD-{order.id} ha cambiado de estado a: {order.status}.\nGracias por confiar en JHIRE 2026."
    send_async_email(
        background_tasks=background_tasks, 
        to_email=order.user.email, 
        subject=f"Actualización de Orden JHIRE (#ORD-{order.id})", 
        content=status_content
    )
    
    background_tasks.add_task(notify_dashboard_refresh)
    
    return order

@router.get("/tprcp/reporte", response_model=None)
def get_tprcp(start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
 
    query = db.query(Order).filter(Order.registration_time_seconds > 0)
    
    if start_date:
        start_d = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(Order.created_at >= start_d)
    if end_date:
        end_d = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query = query.filter(Order.created_at <= end_d)
        
    orders = query.order_by(Order.created_at).all()
    
    daily_orders = {}
    for o in orders:
        if not o.created_at: continue
        d_str = o.created_at.date().isoformat()
        if d_str not in daily_orders:
            daily_orders[d_str] = []
        daily_orders[d_str].append(o)
            
    sorted_days = sorted(daily_orders.keys())
    
    results = []
    total_time = 0
    total_count = 0
    
    for idx, day_str in enumerate(sorted_days, start=1):
        day_list = daily_orders[day_str]
        day_total = sum(o.registration_time_seconds for o in day_list)
        day_avg = day_total // len(day_list)
        
        last_order = day_list[-1]
        tf = last_order.created_at
        from datetime import timedelta
        ti = tf - timedelta(seconds=day_avg)
        
        m, s = divmod(day_avg, 60)
        h, m = divmod(m, 60)
        trcp_str = f"{h:02d}:{m:02d}:{s:02d}"
        
        results.append({
            "item": idx,
            "fecha": tf.strftime("%d/%m/%Y"),
            "tiempo_inicial": ti.strftime("%H:%M:%S"),
            "tiempo_final": tf.strftime("%H:%M:%S"),
            "tiempo_registro": trcp_str,
            "trcp_seconds": day_avg,
            "num_registros": len(day_list)
        })
        total_time += day_avg
        total_count += 1
        
    avg_seconds = total_time / total_count if total_count else 0
    avg_m, avg_s = divmod(int(avg_seconds), 60)
    avg_h, avg_m = divmod(avg_m, 60)
    avg_str = f"{avg_h:02d}:{avg_m:02d}:{avg_s:02d}"
    
    return {
        "data": results,
        "promedio_str": avg_str,
        "promedio_seconds": avg_seconds
    }

from pydantic import BaseModel
class RecommendRequest(BaseModel):
    current_product_ids: List[int]

@router.post("/recommend-products", response_model=None)
def recommend_products(data: RecommendRequest, db: Session = Depends(get_db)):
    if not data.current_product_ids:
        return {"recommendations": []}
        

    current_products = db.query(Product).filter(Product.id.in_(data.current_product_ids)).all()
    categories = list(set([p.category for p in current_products if p.category]))
    recommendations = []
    if categories:
        recs = db.query(Product).filter(
            Product.category.in_(categories),
            ~Product.id.in_(data.current_product_ids),
            Product.stock > 0
        ).limit(2).all()
        for r in recs:
            recommendations.append({
                "id": r.id,
                "name": r.name,
                "price_soles": r.price_soles,
                "image_url": r.image_url,
                "reason": f"Comprados frecuentemente con productos de categoría {r.category}"
            })
            
    if len(recommendations) < 2:
        general_recs = db.query(Product).filter(
            ~Product.id.in_(data.current_product_ids),
            Product.stock > 0
        ).order_by(Product.price_soles.desc()).limit(2).all()
        for r in general_recs:
            if not any(x['id'] == r.id for x in recommendations):
                recommendations.append({
                    "id": r.id,
                    "name": r.name,
                    "price_soles": r.price_soles,
                    "image_url": r.image_url,
                    "reason": "Recomendación general inteligente"
                })
                
    return {"recommendations": recommendations[:2]}
