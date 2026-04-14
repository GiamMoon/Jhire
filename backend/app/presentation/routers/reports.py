from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
import pandas as pd
import os
from ...infrastructure.database import get_db
from ...infrastructure.models import Order, Product

router = APIRouter()

@router.get("/excel")
def export_excel(db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    
    data = []
    for order in orders:
        data.append({
            "Order ID": order.id,
            "User ID": order.user_id,
            "Status": order.status,
            "Total Price": order.total_price,
            "Date": order.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
        
    df = pd.DataFrame(data)
    filepath = "ventas_reporte.xlsx"
    df.to_excel(filepath, index=False)
    
    return FileResponse(filepath, filename="ventas_reporte.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@router.get("/pdf")
def export_pdf(db: Session = Depends(get_db)):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    orders = db.query(Order).limit(50).all()
    filepath = "ventas_reporte.pdf"
    
    c = canvas.Canvas(filepath, pagesize=letter)
    c.drawString(100, 750, "REPORTE DE VENTAS - JHIRE 2026")
    y = 720
    for order in orders:
        c.drawString(100, y, f"Orden: {order.id} | Status: {order.status} | Total: S/. {order.total_price} | Fecha: {order.created_at.strftime('%d/%m/%Y')}")
        y -= 20
        if y < 50:
            c.showPage()
            y = 750
            
    c.save()
    return FileResponse(filepath, filename="ventas_reporte.pdf", media_type="application/pdf")
