from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ...infrastructure.database import get_db
from ...infrastructure.models import User, ClientProfile, CRMInteraction, Order, OrderItem, Product
from ...infrastructure.email import send_async_email, EMAIL_TEMPLATES
from ...infrastructure.security import get_current_user

router = APIRouter()

# =====================================================
# SCHEMAS CRM
# =====================================================

class SendEmailRequest(BaseModel):
    user_id: int
    template: str  # bienvenida, cotizacion, seguimiento, reactivacion
    subject: Optional[str] = None
    custom_message: Optional[str] = None

class CreateInteractionRequest(BaseModel):
    user_id: int
    type: str  # email, whatsapp, llamada, visita
    notes: str

class WhatsAppRequest(BaseModel):
    user_id: int
    message_type: str  # cotizacion, seguimiento, recordatorio_pago, personalizado
    custom_message: Optional[str] = None


# =====================================================
# EXISTING ENDPOINTS
# =====================================================

@router.get("/clients")
def get_clients(db: Session = Depends(get_db)):
    users = db.query(User).filter(User.role != "admin").all()
    
    clients_data = []
    for u in users:
        profile = db.query(ClientProfile).filter(ClientProfile.user_id == u.id).first()
        interactions = db.query(CRMInteraction).filter(CRMInteraction.user_id == u.id).count()
        
        # Get last interaction date
        last_interaction = db.query(CRMInteraction).filter(
            CRMInteraction.user_id == u.id
        ).order_by(CRMInteraction.date.desc()).first()
        
        # Get last order
        last_order = db.query(Order).filter(
            Order.user_id == u.id, Order.status != "Cancelado"
        ).order_by(Order.created_at.desc()).first()
        
        clients_data.append({
            "id": u.id,
            "name": f"{u.first_name} {u.last_name}",
            "email": u.email,
            "phone": u.phone,
            "company": profile.company_name if profile else "N/A",
            "ruc_dni": profile.ruc_dni if profile else "N/A",
            "interactions_count": interactions,
            "consent_29733": profile.data_protection_consent if profile else False,
            "last_interaction_date": last_interaction.date.isoformat() if last_interaction else None,
            "last_order_total": float(last_order.total_price) if last_order else None,
            "last_order_date": last_order.created_at.isoformat() if last_order else None,
        })
    return clients_data

@router.get("/clients/{user_id}/interactions")
def get_interactions(user_id: int, db: Session = Depends(get_db)):
    interactions = db.query(CRMInteraction).filter(CRMInteraction.user_id == user_id).order_by(CRMInteraction.date.desc()).all()
    return [{
        "id": i.id,
        "type": i.type,
        "notes": i.notes,
        "date": i.date.isoformat()
    } for i in interactions]


# =====================================================
# NEW: ENVIAR EMAIL DESDE CRM
# =====================================================

@router.post("/send-email")
def send_crm_email(
    req: SendEmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    
    # Find target user
    target_user = db.query(User).filter(User.id == req.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    client_name = f"{target_user.first_name or ''} {target_user.last_name or ''}".strip() or target_user.email
    
    # Get template
    template_fn = EMAIL_TEMPLATES.get(req.template)
    if not template_fn:
        raise HTTPException(status_code=400, detail=f"Plantilla '{req.template}' no existe. Disponibles: {list(EMAIL_TEMPLATES.keys())}")
    
    # Build email content based on template
    subject_map = {
        "bienvenida": "¡Bienvenido/a a JHIRE 2026!",
        "cotizacion": "Recordatorio: Cotización Pendiente — JHIRE",
        "seguimiento": "Seguimiento Comercial — JHIRE",
        "reactivacion": "¡Te extrañamos! Oferta exclusiva — JHIRE",
    }
    
    subject = req.subject or subject_map.get(req.template, "Comunicación JHIRE 2026")
    
    # Generate HTML body
    if req.template == "bienvenida":
        html_body = template_fn(client_name)
    elif req.template == "cotizacion":
        html_body = template_fn(client_name, req.custom_message or "")
    elif req.template == "seguimiento":
        html_body = template_fn(client_name, req.custom_message or "")
    elif req.template == "reactivacion":
        # Calculate days inactive
        last_order = db.query(Order).filter(
            Order.user_id == req.user_id, Order.status != "Cancelado"
        ).order_by(Order.created_at.desc()).first()
        days = (datetime.utcnow() - last_order.created_at).days if last_order else 30
        html_body = template_fn(client_name, days)
    else:
        html_body = template_fn(client_name)
    
    # Send email
    send_async_email(
        background_tasks=background_tasks,
        to_email=target_user.email,
        subject=subject,
        content=html_body,
        is_html=True
    )
    
    # Auto-register CRM interaction
    interaction = CRMInteraction(
        user_id=req.user_id,
        type="email",
        notes=f"📧 Email automático enviado — Plantilla: {req.template.upper()} | Asunto: {subject} | Operador: {current_user.email}"
    )
    db.add(interaction)
    db.commit()
    
    return {
        "status": "success",
        "message": f"Email '{req.template}' enviado a {target_user.email}",
        "interaction_id": interaction.id,
        "template_used": req.template,
        "recipient": target_user.email
    }


# =====================================================
# NEW: REGISTRAR INTERACCIÓN CRM MANUAL
# =====================================================

@router.post("/interactions")
def create_interaction(
    req: CreateInteractionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    
    target_user = db.query(User).filter(User.id == req.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    valid_types = ["email", "whatsapp", "llamada", "visita", "nota"]
    if req.type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Tipo inválido. Permitidos: {valid_types}")
    
    type_icons = {"email": "📧", "whatsapp": "💬", "llamada": "📞", "visita": "🏢", "nota": "📝"}
    
    interaction = CRMInteraction(
        user_id=req.user_id,
        type=req.type,
        notes=f"{type_icons.get(req.type, '📌')} {req.notes} | Registrado por: {current_user.email}"
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    
    return {
        "status": "success",
        "message": f"Interacción ({req.type}) registrada para cliente #{req.user_id}",
        "interaction": {
            "id": interaction.id,
            "type": interaction.type,
            "date": interaction.date.isoformat()
        }
    }


# =====================================================
# NEW: AI RECOMMENDATIONS FOR CRM
# =====================================================

@router.get("/recommendations/{user_id}")
def get_client_recommendations(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
        
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
    # Get all orders for client
    orders = db.query(Order).filter(Order.user_id == user_id, Order.status != "Cancelado").all()
    total_orders = len(orders)
    total_spent = sum(float(o.total_price) for o in orders)
    avg_ticket = total_spent / total_orders if total_orders > 0 else 0
    
    # Days since last order
    last_order = max((o.created_at for o in orders), default=None)
    days_since_last = (datetime.utcnow() - last_order).days if last_order else None
    
    # AI Segmentation Logic
    segment = "Nuevo Prospecto"
    if total_orders >= 5 and total_spent >= 1000:
        segment = "Cliente VIP"
    elif total_orders >= 2:
        if days_since_last and days_since_last > 60:
            segment = "En Riesgo"
        else:
            segment = "Cliente Frecuente"
    elif total_orders == 1:
        segment = "Cliente Ocasional"
        
    # Generate Recommendations
    recommendations = []
    if segment == "Cliente VIP":
        recommendations = [
            "Contactar para ofrecer productos exclusivos o preventas.",
            "Asignar línea de crédito premium.",
            "Solicitar un testimonio de éxito."
        ]
    elif segment == "En Riesgo":
        recommendations = [
            "Enviar campaña de reactivación con un 15% de descuento.",
            "Realizar llamada de seguimiento para conocer motivos de inactividad."
        ]
    elif segment == "Cliente Frecuente":
        recommendations = [
            "Ofrecer programa de referidos.",
            "Recomendar productos complementarios a sus últimas compras."
        ]
    elif segment == "Cliente Ocasional":
        recommendations = [
            "Enviar boletín de ofertas semanales.",
            "Ofrecer envío gratis en su próxima compra."
        ]
    else:
        recommendations = [
            "Programar llamada de bienvenida y calificación.",
            "Enviar catálogo general de productos top ventas."
        ]
        
    return {
        "metrics": {
            "total_orders": total_orders,
            "total_spent": total_spent,
            "avg_ticket": avg_ticket,
            "days_since_last": days_since_last,
            "segment": segment
        },
        "recommendations": recommendations
    }


# =====================================================
# NEW: WHATSAPP LINK GENERATOR
# =====================================================

import urllib.parse

@router.post("/whatsapp-link")
def generate_whatsapp_link(
    req: WhatsAppRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
        
    target_user = db.query(User).filter(User.id == req.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
    if not target_user.phone:
        raise HTTPException(status_code=400, detail="El cliente no tiene teléfono registrado")
        
    # Clean phone (remove spaces, '+', etc)
    phone = "".join(filter(str.isdigit, target_user.phone))
    if len(phone) == 9 and phone.startswith("9"):
        phone = "51" + phone  # Default to Peru code if standard 9-digit mobile
        
    client_name = target_user.first_name or "Cliente"
    
    msg_map = {
        "cotizacion": f"Hola {client_name}, te comparto la cotización solicitada de JHIRE.",
        "seguimiento": f"Hola {client_name}, te escribo de JHIRE para hacer seguimiento a tus necesidades.",
        "recordatorio_pago": f"Hola {client_name}, te recordamos que tienes un pago pendiente con JHIRE.",
        "personalizado": req.custom_message or f"Hola {client_name},"
    }
    
    msg_text = msg_map.get(req.message_type, f"Hola {client_name},")
    encoded_msg = urllib.parse.quote(msg_text)
    
    wa_url = f"https://wa.me/{phone}?text={encoded_msg}"
    
    # Auto-register interaction
    interaction = CRMInteraction(
        user_id=req.user_id,
        type="whatsapp",
        notes=f"💬 WhatsApp generado — Plantilla: {req.message_type.upper()} | Operador: {current_user.email}"
    )
    db.add(interaction)
    db.commit()
    
    return {
        "status": "success",
        "whatsapp_link": wa_url,
        "message": "Enlace generado"
    }
