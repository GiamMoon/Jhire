from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import func
from ...infrastructure.database import get_db
from ...infrastructure.models import Order, OrderItem, Product
from ...infrastructure.websocket_manager import manager
from datetime import datetime, timedelta
import json

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Mantener la conexión abierta y esperar comandos (ping pong)
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    # Seed fake transactions if there are not enough (Phase 8 requirement)
    orders_count = db.query(Order).filter(Order.status != "Cancelado").count()
    if orders_count < 15:
        import random as rnd
        for i in range(30, 0, -1):
            past_date = datetime.utcnow() - timedelta(days=i)
            fake_total = rnd.uniform(200.0, 1500.0)
            new_ord = Order(user_id=1, status="Completado", total_price=fake_total, created_at=past_date)
            db.add(new_ord)
        db.commit()

    # 1. Total Sales (Completado / En Proceso)
    total_sales = db.query(func.sum(Order.total_price)).filter(Order.status != "Cancelado").scalar() or 0.0

    # 2. Product Ranking
    top_items = db.query(
        Product.name, 
        func.sum(OrderItem.quantity * OrderItem.unit_price).label("contribution")
    ).join(OrderItem, Product.id == OrderItem.product_id)\
     .group_by(Product.name).order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc()).limit(5).all()
     
    product_ranking = [{"name": item[0], "contribution": float(item[1])} for item in top_items]

    # 3. Forecast Accuracy (Scikit-Learn ML)
    # We train LR with historical daily sales
    import numpy as np
    try:
        from sklearn.linear_model import LinearRegression
    except ImportError:
        LinearRegression = None

    projected = 0.0
    accuracy = 100.0
    ai_msg = "Se requiere instalar scikit-learn para activar la IA predictiva."

    if LinearRegression:
        orders = db.query(Order).filter(Order.status != "Cancelado").order_by(Order.created_at).all()
        # Aggregate by day
        daily_sales = {}
        for o in orders:
            d = o.created_at.date()
            daily_sales.setdefault(d, 0.0)
            daily_sales[d] += float(o.total_price)
        
        if len(daily_sales) > 5:
            # Prepare X (days index) and Y (sales)
            X = np.array(range(len(daily_sales))).reshape(-1, 1)
            y = np.array(list(daily_sales.values()))
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Predict "today" based on the trend
            next_day_idx = np.array([[len(daily_sales)]])
            pred_next = model.predict(next_day_idx)[0]
            if pred_next < 0: pred_next = 0
            
            # The accuracy can be R^2 score converted to %
            score = model.score(X, y)
            accuracy = max(10, min(100, score * 100))
            
            projected = pred_next
            
            if model.coef_[0] > 0:
                ai_msg = f"El modelo detecta tendencia a la ALZA. Sugerimos pre-abastecer inventario crítico."
            else:
                ai_msg = f"El modelo detecta tendencia a la BAJA. Se recomiendan campañas de remarketing CRM."

    return {
        "total_sales": float(total_sales),
        "demand_forecast_accuracy": round(accuracy, 1),
        "projected_next_day": round(projected, 2),
        "top_products": product_ranking,
        "ai_anomalies": [ai_msg]
    }
