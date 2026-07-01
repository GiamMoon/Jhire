from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import random
from datetime import datetime, timedelta

from ...infrastructure.database import get_db
from ...domain.schemas import InvoiceCreate, InvoiceResponse
from ...infrastructure.models import Invoice, Order, PaymentInstallment
from ...infrastructure.security import get_current_user, User
from ...domain.schemas import PaymentInstallmentCreate, PaymentInstallmentResponse

router = APIRouter()

@router.get("/tpf/reporte")
def get_tpf_report(start_date: str = None, end_date: str = None, group_days: int = 0, db: Session = Depends(get_db)):
    """
    Agrupa facturas según group_days:
      0 = automático (12 intervalos)
      1 = diario (1 registro por día)
      2,3,5... = cada N días
    """
    from datetime import date as date_type
    
    if start_date:
        s = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        s = date_type(2026, 3, 17)
    if end_date:
        e = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        e = date_type(2026, 4, 15)
    
    total_days = (e - s).days + 1
    
    # Build intervals based on group_days
    intervals = []
    if group_days <= 0:
        # Original: 12 fixed intervals
        num_intervals = 12
        days_per_interval = total_days / num_intervals
        for i in range(num_intervals):
            int_start = s + timedelta(days=int(i * days_per_interval))
            int_end = s + timedelta(days=int((i + 1) * days_per_interval) - 1)
            if i == num_intervals - 1:
                int_end = e
            intervals.append((int_start, int_end))
    else:
        # User-defined grouping by N days
        current = s
        while current <= e:
            int_end = min(current + timedelta(days=group_days - 1), e)
            intervals.append((current, int_end))
            current = int_end + timedelta(days=1)
    
    results = []
    for idx, (int_start, int_end) in enumerate(intervals, start=1):
        invoices = db.query(Invoice).filter(
            Invoice.issue_date >= datetime.combine(int_start, datetime.min.time()),
            Invoice.issue_date <= datetime.combine(int_end, datetime.max.time()),
            Invoice.processing_time_seconds > 0
        ).all()
        
        total_seconds = sum(inv.processing_time_seconds for inv in invoices)
        count = len(invoices)
        total_mins = round(total_seconds / 60, 2)
        avg_mins = round(total_mins / count, 2) if count > 0 else 0
        
        results.append({
            "item": idx,
            "fecha_emision": int_start.strftime("%d/%m/%Y"),
            "fecha_finalizacion": int_end.strftime("%d/%m/%Y"),
            "tiempo_total_procesamiento": total_mins,
            "numero_total_facturas": count,
            "tiempo_procesamiento": avg_mins
        })
        
    return {"data": results}

@router.post("/emitir")
def emitir_factura_sunat(invoice_data: InvoiceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Endpoint mejorado que simula el proceso completo de emisión electrónica
    con OSE/PSE SUNAT, retornando metadatos detallados del procesamiento.
    """
    import time
    import hashlib
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    
    if not invoice_data.client_name or len(invoice_data.client_name.strip()) < 3:
        raise HTTPException(status_code=422, detail="Razón Social / Nombres debe tener al menos 3 caracteres")
    
    start_time = time.time()
    steps = []
    
    # PASO 1: Validación de datos de entrada (Pydantic)
    step1_start = time.time()
    order = db.query(Order).filter(Order.id == invoice_data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada en el sistema")
    existing = db.query(Invoice).filter(Invoice.order_id == invoice_data.order_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"La orden #{invoice_data.order_id} ya tiene comprobante: {existing.invoice_number}")
    if order.total_price <= 0:
        raise HTTPException(status_code=422, detail="El monto de la orden debe ser positivo")
    steps.append({"step": "Validación Pydantic-Core", "time_ms": round((time.time() - step1_start) * 1000, 1), "status": "OK"})
    
    # PASO 2: Cálculo tributario IGV 18%
    step2_start = time.time()
    subtotal = round(float(order.total_price) / 1.18, 2)
    igv = round(float(order.total_price) - subtotal, 2)
    ruc_dni = invoice_data.client_ruc_dni.strip()
    serie = "F001" if len(ruc_dni) == 11 else "B001"
    doc_type = "Factura Electrónica" if serie == "F001" else "Boleta de Venta Electrónica"
    steps.append({"step": "Cálculo tributario IGV (18%)", "time_ms": round((time.time() - step2_start) * 1000, 1), "status": "OK"})
    
    # PASO 3: Generación de XML UBL 2.1
    step3_start = time.time()
    last_invoice = db.query(Invoice).filter(
        Invoice.invoice_number.like(f"{serie}-%"),
        Invoice.invoice_number.not_like("%EXTRA%")
    ).order_by(Invoice.id.desc()).first()
    next_num = (int(last_invoice.invoice_number.split('-')[1]) + 1) if last_invoice else 1
    invoice_num = f"{serie}-{str(next_num).zfill(8)}"
    xml_hash = hashlib.sha256(f"{invoice_num}{subtotal}{igv}{ruc_dni}{datetime.utcnow().isoformat()}".encode()).hexdigest()
    steps.append({"step": "Generación XML UBL 2.1", "time_ms": round((time.time() - step3_start) * 1000, 1), "status": "OK"})
    
    # PASO 4: Firma digital del comprobante
    step4_start = time.time()
    time.sleep(random.uniform(0.3, 0.6))  # Simular firma
    signature_value = hashlib.sha512(xml_hash.encode()).hexdigest()[:64]
    steps.append({"step": "Firma Digital (SHA-512)", "time_ms": round((time.time() - step4_start) * 1000, 1), "status": "OK"})
    
    # PASO 5: Envío a OSE/PSE SUNAT
    step5_start = time.time()
    time.sleep(random.uniform(0.8, 1.8))  # Simular conexión SUNAT
    cdr_code = f"0{random.randint(100, 999)}"
    cdr_description = "La Factura numero " + invoice_num + ", ha sido aceptada"
    steps.append({"step": "Envío a OSE SUNAT", "time_ms": round((time.time() - step5_start) * 1000, 1), "status": "OK"})
    
    # PASO 6: Recepción de CDR (Constancia de Recepción)
    step6_start = time.time()
    time.sleep(random.uniform(0.2, 0.5))
    steps.append({"step": "CDR Recibida (Aceptada)", "time_ms": round((time.time() - step6_start) * 1000, 1), "status": "OK"})
    
    elapsed_seconds = int(time.time() - start_time)
    
    # Guardar en DB
    new_inv = Invoice(
        order_id=invoice_data.order_id,
        invoice_number=invoice_num,
        client_ruc_dni=ruc_dni,
        client_name=invoice_data.client_name.strip().upper(),
        subtotal=subtotal,
        igv=igv,
        total=float(order.total_price),
        sunat_status="Aceptada",
        processing_time_seconds=elapsed_seconds
    )
    db.add(new_inv)
    db.commit()
    db.refresh(new_inv)
    
    total_time = round((time.time() - start_time) * 1000, 1)
    
    return {
        "invoice": {
            "id": new_inv.id,
            "invoice_number": invoice_num,
            "doc_type": doc_type,
            "serie": serie,
            "client_ruc_dni": ruc_dni,
            "client_name": new_inv.client_name,
            "subtotal": subtotal,
            "igv": igv,
            "total": new_inv.total,
            "issue_date": new_inv.issue_date.strftime("%d/%m/%Y %H:%M:%S"),
        },
        "sunat": {
            "status": "ACEPTADA",
            "cdr_code": cdr_code,
            "cdr_description": cdr_description,
            "xml_hash": xml_hash[:40],
            "signature": signature_value[:40],
            "processing_steps": steps,
            "total_time_ms": total_time,
            "total_time_seconds": round(total_time / 1000, 2)
        }
    }

@router.post("/", response_model=InvoiceResponse)
def generate_invoice(invoice_data: InvoiceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    
    # Validate client name is not empty or too short
    if not invoice_data.client_name or len(invoice_data.client_name.strip()) < 3:
        raise HTTPException(status_code=422, detail="Razón Social / Nombres debe tener al menos 3 caracteres")
        
    order = db.query(Order).filter(Order.id == invoice_data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada en el sistema")
    
    # Check for duplicate invoice for same order
    existing = db.query(Invoice).filter(Invoice.order_id == invoice_data.order_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"La orden #{invoice_data.order_id} ya tiene un comprobante emitido: {existing.invoice_number}")
    
    # Validate order total is positive
    if order.total_price <= 0:
        raise HTTPException(status_code=422, detail="El monto de la orden debe ser positivo para emitir comprobante")
        
    # SUNAT Compliance: Calculate IGV 18%
    subtotal = round(float(order.total_price) / 1.18, 2)
    igv = round(float(order.total_price) - subtotal, 2)
    
    # SUNAT: Determine document type (Factura for RUC 11 digits, Boleta for DNI 8 digits)
    ruc_dni = invoice_data.client_ruc_dni.strip()
    if len(ruc_dni) == 11:
        serie = "F001"  # Factura Electrónica
    else:
        serie = "B001"  # Boleta de Venta Electrónica
    
    # Sequential numbering per series
    last_invoice = db.query(Invoice).filter(
        Invoice.invoice_number.like(f"{serie}-%"),
        Invoice.invoice_number.not_like("%EXTRA%")
    ).order_by(Invoice.id.desc()).first()
    
    if last_invoice:
        last_num = int(last_invoice.invoice_number.split('-')[1])
        next_num = last_num + 1
    else:
        next_num = 1
    
    invoice_num = f"{serie}-{str(next_num).zfill(8)}"
    
    new_inv = Invoice(
        order_id=invoice_data.order_id,
        invoice_number=invoice_num,
        client_ruc_dni=ruc_dni,
        client_name=invoice_data.client_name.strip().upper(),
        subtotal=subtotal,
        igv=igv,
        total=float(order.total_price),
        sunat_status="Emitida"
    )
    db.add(new_inv)
    db.commit()
    db.refresh(new_inv)
    return new_inv

@router.get("/", response_model=List[InvoiceResponse])
def get_invoices(db: Session = Depends(get_db)):
    return db.query(Invoice).order_by(Invoice.issue_date.desc()).all()

@router.get("/{invoice_id}/ubl", response_model=str)
def generate_ubl_xml(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    # Mock UBL 2.1 string template
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
    <cbc:ID>{invoice.invoice_number}</cbc:ID>
    <cbc:IssueDate>{invoice.issue_date.strftime('%Y-%m-%d')}</cbc:IssueDate>
    <cbc:InvoiceTypeCode>01</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>PEN</cbc:DocumentCurrencyCode>
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="6">{invoice.client_ruc_dni}</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>{invoice.client_name}</cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingCustomerParty>
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="PEN">{invoice.subtotal}</cbc:LineExtensionAmount>
        <cbc:TaxInclusiveAmount currencyID="PEN">{invoice.total}</cbc:TaxInclusiveAmount>
    </cac:LegalMonetaryTotal>
</Invoice>"""
    return xml

@router.post("/{invoice_id}/installments", response_model=PaymentInstallmentResponse)
def add_installment(invoice_id: int, data: PaymentInstallmentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
        
    payment = PaymentInstallment(
        invoice_id=invoice_id,
        amount=data.amount,
        due_date=data.due_date,
        status="Pendiente"
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment

@router.put("/installments/{payment_id}/pay", response_model=PaymentInstallmentResponse)
def mark_installment_paid(payment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    
    payment = db.query(PaymentInstallment).filter(PaymentInstallment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Cuota no encontrada")
        
    payment.status = "Pagado"
    payment.paid_date = datetime.utcnow()
    db.commit()
    db.refresh(payment)
    return payment




@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(invoice_id: int, db: Session = Depends(get_db)):
    from fastapi.responses import FileResponse
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    import os
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    # Determine document type
    doc_type = "FACTURA ELECTRÓNICA" if invoice.invoice_number.startswith("F") else "BOLETA DE VENTA ELECTRÓNICA"
    id_label = "RUC" if len(invoice.client_ruc_dni) == 11 else "DNI"
        
    filepath = f"factura_{invoice.invoice_number}.pdf"
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    
    # -----------------------------
    # 1. EMISOR Y RECUADRO SUNAT
    # -----------------------------
    c.setFont("Helvetica-Bold", 24)
    c.drawString(40, height - 60, "JHIRE S.A.C.")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 75, "Av. Industrial 1234, Lima, Perú")
    c.drawString(40, height - 90, "Teléfono: (01) 555-1234")
    c.drawString(40, height - 105, "contacto@jhire.com.pe")
    
    # Recuadro Derecho SUNAT
    c.setLineWidth(1)
    c.rect(width - 260, height - 120, 220, 80)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width - 150, height - 60, "RUC: 20123456789")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width - 150, height - 80, doc_type)
    c.setFont("Helvetica", 14)
    c.drawCentredString(width - 150, height - 100, f"{invoice.invoice_number}")
    
    # -----------------------------
    # 2. DATOS DEL CLIENTE
    # -----------------------------
    c.roundRect(40, height - 210, width - 80, 70, 5)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 160, "SEÑOR(ES):")
    c.drawString(50, height - 175, f"{id_label}:")
    c.drawString(50, height - 190, "FECHA EMISIÓN:")
    
    c.setFont("Helvetica", 10)
    c.drawString(140, height - 160, f"{invoice.client_name}")
    c.drawString(140, height - 175, f"{invoice.client_ruc_dni}")
    c.drawString(140, height - 190, f"{invoice.issue_date.strftime('%d/%m/%Y')}")
    
    # Moneda
    c.setFont("Helvetica-Bold", 10)
    c.drawString(width - 200, height - 175, "MONEDA:")
    c.setFont("Helvetica", 10)
    c.drawString(width - 140, height - 175, "SOLES (PEN)")
    
    # Tipo de documento
    c.setFont("Helvetica-Bold", 10)
    c.drawString(width - 200, height - 160, "TIPO DOC:")
    c.setFont("Helvetica", 10)
    c.drawString(width - 140, height - 160, id_label)
    
    # -----------------------------
    # 3. DETALLE DE ÍTEMS
    # -----------------------------
    c.setFillColor(colors.HexColor("#003461"))
    c.rect(40, height - 250, width - 80, 20, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 245, "CANT")
    c.drawString(100, height - 245, "DESCRIPCIÓN")
    c.drawString(380, height - 245, "V. UNIT")
    c.drawString(480, height - 245, "IMPORTE")
    
    # Contenido
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    y_item = height - 270
    c.drawString(55, y_item, "1.00")
    c.drawString(100, y_item, f"Consolidado de ítems — Orden Comercial #{invoice.order_id}")
    c.drawString(380, y_item, f"S/ {invoice.subtotal:.2f}")
    c.drawString(480, y_item, f"S/ {invoice.subtotal:.2f}")
    
    # Tabla borde
    c.rect(40, height - 500, width - 80, 250)
    
    # -----------------------------
    # 4. TOTALES
    # -----------------------------
    c.setFillColor(colors.HexColor("#f2f4ff"))
    c.rect(width - 230, height - 580, 190, 70, fill=1)
    c.setFillColor(colors.black)
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(width - 220, height - 530, "OP. GRAVADAS:")
    c.drawString(width - 220, height - 545, "IGV (18%):")
    c.drawString(width - 220, height - 565, "IMPORTE TOTAL:")
    
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 50, height - 530, f"S/ {invoice.subtotal:.2f}")
    c.drawRightString(width - 50, height - 545, f"S/ {invoice.igv:.2f}")
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - 50, height - 565, f"S/ {invoice.total:.2f}")
    
    # Monto en letras (simplified)
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(40, height - 520, f"SON: {int(invoice.total)} CON {int(round((invoice.total % 1) * 100, 0)):02d}/100 SOLES")
    
    # Hash de integridad
    import hashlib
    hash_val = hashlib.sha256(f"{invoice.invoice_number}{invoice.total}{invoice.issue_date}".encode()).hexdigest()[:20]
    c.setFont("Helvetica", 7)
    c.drawString(40, height - 600, f"Hash de Integridad: {hash_val.upper()}")
    
    # Footer Legal
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, 60, f"Representación Impresa de la {doc_type}.")
    c.drawCentredString(width / 2, 48, "Autorizado mediante Resolución de Intendencia N° 0340050006573/SUNAT")
    c.drawCentredString(width / 2, 36, "Consulte su validez en www.sunat.gob.pe — Generado por JHIRE ERP 2026")
    
    c.save()
    return FileResponse(filepath, filename=f"comprobante_{invoice.invoice_number}.pdf", media_type="application/pdf")
