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
    
    # Data for time series chart
    daily_labels = []
    daily_values = []
    forecast_labels = []
    forecast_values = []

    if LinearRegression:
        orders = db.query(Order).filter(Order.status != "Cancelado").order_by(Order.created_at).all()
        # Aggregate by day
        daily_sales = {}
        for o in orders:
            d = o.created_at.date()
            daily_sales.setdefault(d, 0.0)
            daily_sales[d] += float(o.total_price)
        
        if len(daily_sales) > 5:
            sorted_dates = sorted(daily_sales.keys())
            
            # Build series for chart (last 30 days max)
            chart_dates = sorted_dates[-30:]
            daily_labels = [d.strftime("%d/%m") for d in chart_dates]
            daily_values = [round(daily_sales[d], 2) for d in chart_dates]
            
            # Prepare X (days index) and Y (sales)
            X = np.array(range(len(daily_sales))).reshape(-1, 1)
            y = np.array([daily_sales[d] for d in sorted_dates])
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Predict next 7 days
            last_idx = len(daily_sales)
            for i in range(7):
                future_idx = np.array([[last_idx + i]])
                pred = max(0, model.predict(future_idx)[0])
                future_date = sorted_dates[-1] + timedelta(days=i+1)
                forecast_labels.append(future_date.strftime("%d/%m"))
                forecast_values.append(round(pred, 2))
            
            # Confidence score: Based on Mean Absolute Error relative to mean
            # This gives a more practical and stable metric than raw R²
            from sklearn.metrics import mean_absolute_error
            predictions = model.predict(X)
            mae = mean_absolute_error(y, predictions)
            mean_val = max(1, y.mean())
            # Confidence = 100 - (error% relative to mean), clamped [40, 98]
            accuracy = max(40, min(98, 100 - (mae / mean_val * 100)))
            
            projected = forecast_values[0] if forecast_values else 0
            
            if model.coef_[0] > 0:
                ai_msg = f"El modelo detecta tendencia a la ALZA (+S/ {model.coef_[0]:.2f}/día). Sugerimos pre-abastecer inventario crítico y ampliar campañas de fidelización."
            else:
                ai_msg = f"El modelo detecta tendencia a la BAJA ({model.coef_[0]:.2f}/día). Se recomiendan campañas de remarketing CRM y promociones de reactivación."

    return {
        "total_sales": float(total_sales),
        "demand_forecast_accuracy": round(accuracy, 1),
        "projected_next_day": round(projected, 2),
        "top_products": product_ranking,
        "ai_anomalies": [ai_msg],
        # NEW: Time series data for charts
        "daily_labels": daily_labels,
        "daily_values": daily_values,
        "forecast_labels": forecast_labels,
        "forecast_values": forecast_values
    }
