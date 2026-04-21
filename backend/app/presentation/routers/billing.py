from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import random
from datetime import datetime

from ...infrastructure.database import get_db
from ...domain.schemas import InvoiceCreate, InvoiceResponse
from ...infrastructure.models import Invoice, Order, PaymentInstallment
from ...infrastructure.security import get_current_user, User
from ...domain.schemas import PaymentInstallmentCreate, PaymentInstallmentResponse

router = APIRouter()

@router.post("/", response_model=InvoiceResponse)
def generate_invoice(invoice_data: InvoiceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
        
    order = db.query(Order).filter(Order.id == invoice_data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
        
    # SUNAT Compliance Logic (Mock)
    subtotal = round(order.total_price / 1.18, 2)
    igv = round(order.total_price - subtotal, 2)
    
    invoice_num = f"F001-{random.randint(100000, 999999)}"
    
    new_inv = Invoice(
        order_id=invoice_data.order_id,
        invoice_number=invoice_num,
        client_ruc_dni=invoice_data.client_ruc_dni,
        client_name=invoice_data.client_name,
        subtotal=subtotal,
        igv=igv,
        total=order.total_price,
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
        
    filepath = f"factura_{invoice.invoice_number}.pdf"
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    
    # -----------------------------
    # 1. EMISOR Y RECUADRO SUNAT
    # -----------------------------
    # Logo / Nombre Empresa Izquierda
    c.setFont("Helvetica-Bold", 24)
    c.drawString(40, height - 60, "JHIRE S.A.C.")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 75, "Av. Industrial 1234, Lima, Perú")
    c.drawString(40, height - 90, "Teléfono: (01) 555-1234")
    c.drawString(40, height - 105, "contacto@jhire.com.pe")
    
    # Recuadro Derecho SUNAT
    c.setLineWidth(1)
    c.rect(width - 250, height - 120, 200, 80)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width - 150, height - 60, "RUC: 20123456789")
    c.drawCentredString(width - 150, height - 80, "FACTURA ELECTRÓNICA")
    c.setFont("Helvetica", 14)
    c.drawCentredString(width - 150, height - 100, f"{invoice.invoice_number}")
    
    # -----------------------------
    # 2. DATOS DEL CLIENTE
    # -----------------------------
    c.roundRect(40, height - 210, width - 80, 70, 5)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 160, "SEÑOR(ES):")
    c.drawString(50, height - 175, "RUC/DNI:")
    c.drawString(50, height - 190, "FECHA EMISIÓN:")
    
    c.setFont("Helvetica", 10)
    c.drawString(130, height - 160, f"{invoice.client_name}")
    c.drawString(130, height - 175, f"{invoice.client_ruc_dni}")
    c.drawString(130, height - 190, f"{invoice.issue_date.strftime('%Y-%m-%d')}")
    
    # Moneda
    c.setFont("Helvetica-Bold", 10)
    c.drawString(width - 200, height - 190, "MONEDA:")
    c.setFont("Helvetica", 10)
    c.drawString(width - 140, height - 190, "SOLES (PEN)")
    
    # -----------------------------
    # 3. DETALLE DE ÍTEMS
    # -----------------------------
    # Cabecera Tabla
    c.setFillColor(colors.lightgrey)
    c.rect(40, height - 250, width - 80, 20, fill=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 245, "CANT")
    c.drawString(100, height - 245, "DESCRIPCIÓN")
    c.drawString(400, height - 245, "V. UNIT")
    c.drawString(480, height - 245, "IMPORTE")
    
    # Contenido (1 item genérico apuntando al Order)
    c.setFont("Helvetica", 10)
    y_item = height - 270
    c.drawString(55, y_item, "1.00")
    c.drawString(100, y_item, f"Consolidados de venta e ítems según Orden Comercial #{invoice.order_id}")
    c.drawString(400, y_item, f"S/ {invoice.subtotal:.2f}")
    c.drawString(480, y_item, f"S/ {invoice.subtotal:.2f}")
    
    # Líneas de la tabla
    c.rect(40, height - 500, width - 80, 250)
    
    # -----------------------------
    # 4. TOTALES
    # -----------------------------
    # Recuadro Totales (Abajo a la derecha)
    c.rect(width - 220, height - 580, 180, 60)
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(width - 210, height - 540, "OP. GRAVADAS:")
    c.drawString(width - 210, height - 555, "IGV (18%):")
    c.drawString(width - 210, height - 570, "IMPORTE TOTAL:")
    
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 50, height - 540, f"S/ {invoice.subtotal:.2f}")
    c.drawRightString(width - 50, height - 555, f"S/ {invoice.igv:.2f}")
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 50, height - 570, f"S/ {invoice.total:.2f}")
    
    # Son:
    c.setFont("Helvetica", 9)
    c.drawString(40, height - 530, f"SON: AUTOMATIZADO CON EXPRESIÓN NUMÉRICA SOLES")
    
    # Footer Legal
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, 50, "Representación Impresa de la FACTURA ELECTRÓNICA. Consúltela en la clave SOL.")
    c.drawCentredString(width / 2, 40, "Generado por JHIRE ERP 2026.")
    
    c.save()
    return FileResponse(filepath, filename=f"factura_{invoice.invoice_number}.pdf", media_type="application/pdf")
