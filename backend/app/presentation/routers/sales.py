from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.infrastructure.models import Order
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/tprvp/reporte")
def get_tprvp(start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    query = db.query(Order).filter(
        Order.status == "Completado",
        Order.sale_confirmation_seconds > 0,
        Order.completed_at != None
    )
    
    if start_date:
        start_d = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(Order.completed_at >= start_d)
    if end_date:
        end_d = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query = query.filter(Order.completed_at <= end_d)
        
    orders = query.order_by(Order.completed_at).all()
    
    daily_orders = {}
    for o in orders:
        if not o.completed_at: continue
        d_str = o.completed_at.date().isoformat()
        if d_str not in daily_orders:
            daily_orders[d_str] = []
        daily_orders[d_str].append(o)
            
    sorted_days = sorted(daily_orders.keys())
    
    results = []
    total_time = 0
    total_count = 0
    
    for idx, day_str in enumerate(sorted_days, start=1):
        day_list = daily_orders[day_str]
        day_total = sum(o.sale_confirmation_seconds for o in day_list)
        day_avg = day_total // len(day_list)
        
        last_order = day_list[-1]
        tf = last_order.completed_at
        ti = tf - timedelta(seconds=day_avg)
        
        m, s = divmod(day_avg, 60)
        h, m = divmod(m, 60)
        trvp_str = f"{h:02d}:{m:02d}:{s:02d}"
        
        results.append({
            "item": idx,
            "fecha": tf.strftime("%d/%m/%Y"),
            "tiempo_inicial": ti.strftime("%H:%M:%S"),
            "tiempo_final": tf.strftime("%H:%M:%S"),
            "tiempo_registro": trvp_str,
            "trvp_seconds": day_avg,
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

@router.get("/")
def get_sales_data():
    return {
        "funnel": {
            "total_value": 1200000,
            "avg_cycle_days": 14,
            "conversion_pct": 7.4
        },
        "quarterly_target": 78,
        "remaining_amount": 240000,
        "recent_activity": [
            {"date": "Oct 24, 14:20", "client": "Global Automotriz S.A.", "type": "Industrial Supply"},
            {"date": "Oct 24, 11:05", "client": "Textiles del Norte", "type": "Manufacturer"},
            {"date": "Oct 23, 16:45", "client": "Logística Integral S.C.", "type": "Warehouse Operations"},
            {"date": "Oct 23, 09:12", "client": "Minería del Pacífico", "type": "Industrial Mining"}
        ],
        "ai_insight": "Historical data suggests an increase in demand for Synthetic Nylon Brushes in the textile sector over the next 15 days. We recommend proactive outreach to Top 5 clients."
    }
