import re

path = r"d:\tesis\jhire\backend\app\presentation\routers\reports.py"
with open(path, "r", encoding="utf-8") as f:
    reports_code = f.read()

new_reports_code = """from fastapi import APIRouter, Depends
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
            "Código de Órden": f"JHIRE-{order.id}",
            "ID Usuario Cliente": order.user_id,
            "Estado Transaccional": order.status.upper(),
            "Monto Total Ingresado": f"S/ {order.total_price:.2f}",
            "Fecha Efectiva": order.created_at.strftime("%d/%m/%Y %H:%M:%S")
        })
        
    df = pd.DataFrame(data)
    filepath = "ventas_corporativo_jhire.xlsx"
    df.to_excel(filepath, index=False)
    
    return FileResponse(filepath, filename="ventas_corporativo_jhire.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@router.get("/pdf")
def export_pdf(db: Session = Depends(get_db)):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.piecharts import Pie
    
    orders = db.query(Order).limit(200).all()
    filepath = "informe_ejecutivo_jhire.pdf"
    
    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=50, bottomMargin=50)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        name="TitleCustom",
        parent=styles['Heading1'],
        fontName="Helvetica-Bold",
        fontSize=20,
        alignment=1, # Center
        spaceAfter=20,
        textColor=colors.HexColor("#003461")
    )
    
    subtitle_style = ParagraphStyle(
        name="SubTitleCustom",
        parent=styles['Normal'],
        fontName="Helvetica",
        fontSize=12,
        alignment=1,
        spaceAfter=30,
        textColor=colors.gray
    )
    
    story.append(Paragraph("REPORTE EJECUTIVO DE VENTAS - JHIRE 2026", title_style))
    story.append(Paragraph(f"Informe extraído y auditado algorítmicamente. Base de datos actual: {len(orders)} órdenes recientes.", subtitle_style))
    
    # Calculate Data for PieChart
    status_counts = {}
    for o in orders:
        status_counts[o.status] = status_counts.get(o.status, 0) + 1
        
    if status_counts:
        story.append(Paragraph("<b>DISTRIBUCIÓN DE ÓRDENES POR ESTADO</b>", styles["Heading3"]))
        story.append(Spacer(1, 10))
        
        drawing = Drawing(300, 200)
        pie = Pie()
        pie.x = 80
        pie.y = 20
        pie.width = 150
        pie.height = 150
        pie.data = list(status_counts.values())
        pie.labels = [f"{k} ({v})" for k, v in status_counts.items()]
        
        # JHIRE Colors
        color_palette = [colors.HexColor("#003461"), colors.HexColor("#16a34a"), colors.HexColor("#ba1a1a"), colors.HexColor("#727781")]
        for i in range(len(pie.data)):
            pie.slices[i].fillColor = color_palette[i % len(color_palette)]
            
        pie.sideLabels = 1
        drawing.add(pie)
        story.append(drawing)
        story.append(Spacer(1, 30))
        
    # Build Table Data
    story.append(Paragraph("<b>DETALLE DE TRANSACCIONES HISTÓRICAS</b>", styles["Heading3"]))
    story.append(Spacer(1, 10))
    
    table_data = [["ORDEN ID", "ESTADO", "MONTO S/", "FECHA"]]
    total_rev = 0
    for o in orders:
        table_data.append([
            f"#{o.id}",
            o.status,
            f"S/. {o.total_price:.2f}",
            o.created_at.strftime('%d/%m/%Y')
        ])
        total_rev += float(o.total_price)
        
    table_data.append(["", "TOTAL INGRESOS:", f"S/. {total_rev:.2f}", ""])
    
    t = Table(table_data, colWidths=[80, 150, 150, 100])
    
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003461")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        
        # Zebra Stripes
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor("#f2f4ff")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor("#f2f4ff")]),
        ('GRID', (0, 0), (-1, -2), 1, colors.HexColor("#c2c7d1")),
        
        # Total Row Format
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#eaedff")),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor("#003461")),
        ('ALIGN', (2, -1), (2, -1), 'CENTER'),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor("#003461")),
    ]))
    
    story.append(t)
    
    doc.build(story)
    
    return FileResponse(filepath, filename="informe_ejecutivo_jhire.pdf", media_type="application/pdf")
"""

with open(path, "w", encoding="utf-8") as f:
    f.write(new_reports_code)
    
print("Replaced reports.py successfully")
