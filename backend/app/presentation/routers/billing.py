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
