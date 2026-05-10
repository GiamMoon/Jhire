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
            "notes": interaction.notes,
            "date": interaction.date.isoformat()
        }
    }


# =====================================================
# NEW: GENERAR LINK WHATSAPP PRE-ARMADO
# =====================================================

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
        raise HTTPException(status_code=400, detail="El cliente no tiene número de teléfono registrado")
    
    client_name = f"{target_user.first_name or ''} {target_user.last_name or ''}".strip() or "Estimado/a cliente"
    
    # Build message based on type
    messages = {
        "cotizacion": (
            f"Hola {client_name}, le saluda el equipo comercial de *JHIRE*. 🏭\n\n"
            f"Le recordamos que tiene una cotización pendiente de revisión en nuestra plataforma. "
            f"Las cotizaciones tienen una validez de 15 días.\n\n"
            f"📋 Puede revisar el detalle en: http://localhost:8000/mis_pedidos.html\n\n"
            f"¿Tiene alguna consulta sobre los productos o desea ajustar cantidades? "
            f"Estamos para ayudarle.\n\n"
            f"_Equipo Comercial JHIRE_"
        ),
        "seguimiento": (
            f"Hola {client_name}, le saluda *JHIRE*. 🤝\n\n"
            f"Queremos asegurarnos de que su último pedido haya llegado en perfectas condiciones. "
            f"¿Cómo fue su experiencia con nuestros productos?\n\n"
            f"Su opinión es muy importante para nosotros y nos ayuda a mejorar nuestro servicio industrial.\n\n"
            f"_Equipo de Atención al Cliente JHIRE_"
        ),
        "recordatorio_pago": (
            f"Hola {client_name}, le saluda el área de cobranzas de *JHIRE*. 📋\n\n"
            f"Le recordamos amablemente que tiene una cuota de pago pendiente asociada a su factura. "
            f"Le invitamos a regularizar el pago para mantener su línea de crédito activa.\n\n"
            f"📞 Para consultas, comuníquese con nosotros al (01) 555-1234.\n\n"
            f"_Área de Cobranzas JHIRE_"
        ),
        "personalizado": req.custom_message or f"Hola {client_name}, le saluda *JHIRE*.",
    }
    
    message = messages.get(req.message_type, messages["personalizado"])
    
    # Clean phone number
    import re
    phone_clean = re.sub(r'\D', '', target_user.phone)
    if not phone_clean.startswith('51') and len(phone_clean) == 9:
        phone_clean = '51' + phone_clean  # Peru country code
    
    # URL encode message
    from urllib.parse import quote
    wa_link = f"https://wa.me/{phone_clean}?text={quote(message)}"
    
    # Auto-register CRM interaction
    interaction = CRMInteraction(
        user_id=req.user_id,
        type="whatsapp",
        notes=f"💬 WhatsApp enviado — Tipo: {req.message_type.upper()} | Operador: {current_user.email}"
    )
    db.add(interaction)
    db.commit()
    
    return {
        "status": "success",
        "whatsapp_link": wa_link,
        "phone": phone_clean,
        "message_preview": message[:200] + "..." if len(message) > 200 else message,
        "message_type": req.message_type,
        "interaction_id": interaction.id
    }


# =====================================================
# EXISTING: RECOMENDACIONES IA
# =====================================================

@router.get("/recommendations/{user_id}")
def get_recommendations(user_id: int, db: Session = Depends(get_db)):
    """
    Análisis Predictivo de Comportamiento del Consumidor.
    Analiza patrones de compra (frecuencia, recencia, ticket promedio, 
    categorías preferidas) para sugerir acciones comerciales proactivas.
    """
    orders = db.query(Order).filter(
        Order.user_id == user_id, 
        Order.status != "Cancelado"
    ).order_by(Order.created_at.desc()).all()
    
    recommendations = []
    segment = "Nuevo Prospecto"
    
    if not orders:
        segment = "Nuevo Prospecto"
        recommendations = [
            "🎯 Cliente sin historial de compras. Activar secuencia de bienvenida B2B.",
            "📧 Programar email automatizado con catálogo de productos más vendidos.",
            "📞 Asignar llamada de prospección dentro de las próximas 48 horas."
        ]
    else:
        total_spent = sum([float(o.total_price) for o in orders])
        total_orders = len(orders)
        avg_ticket = total_spent / total_orders if total_orders > 0 else 0
        
        # Recencia: Días desde la última compra
        last_order_date = orders[0].created_at
        days_since_last = (datetime.utcnow() - last_order_date).days
        
        # Frecuencia: Compras por mes (basado en rango de fechas)
        first_order_date = orders[-1].created_at
        months_active = max(1, (datetime.utcnow() - first_order_date).days / 30)
        freq_per_month = total_orders / months_active
        
        # Productos más comprados por este cliente
        top_products = db.query(
            Product.name,
            func.sum(OrderItem.quantity).label("qty")
        ).join(OrderItem, Product.id == OrderItem.product_id)\
         .join(Order, Order.id == OrderItem.order_id)\
         .filter(Order.user_id == user_id, Order.status != "Cancelado")\
         .group_by(Product.name)\
         .order_by(func.sum(OrderItem.quantity).desc())\
         .limit(3).all()
        
        fav_products = [p[0] for p in top_products] if top_products else []
        
        # --- SEGMENTACIÓN POR COMPORTAMIENTO ---
        
        # VIP: Alto gasto + alta frecuencia
        if total_spent > 5000 and freq_per_month >= 1:
            segment = "Cliente VIP"
            recommendations.append(
                f"💎 Cliente de alto valor (LTV: S/ {total_spent:,.2f}). Ticket promedio: S/ {avg_ticket:,.2f}."
            )
            recommendations.append(
                "🏆 Migrar a programa de fidelización Premium con descuentos escalonados del 5-15%."
            )
            if days_since_last > 15:
                recommendations.append(
                    f"⚠️ Última compra hace {days_since_last} días. Activar campaña de retención urgente."
                )
            else:
                recommendations.append(
                    "✅ Actividad reciente confirmada. Mantener seguimiento de satisfacción post-venta."
                )
        
        # En Riesgo: Compró antes pero lleva mucho sin comprar
        elif days_since_last > 30:
            segment = "En Riesgo"
            recommendations.append(
                f"🚨 Sin actividad hace {days_since_last} días. Riesgo de abandono detectado."
            )
            recommendations.append(
                f"📉 Frecuencia histórica: {freq_per_month:.1f} compras/mes → Patrón degradado."
            )
            recommendations.append(
                "📧 Enviar oferta personalizada de reactivación con descuento del 10% en su categoría favorita."
            )
            if fav_products:
                recommendations.append(
                    f"🔄 Re-abastecimiento sugerido: {', '.join(fav_products[:2])} (productos más solicitados)."
                )
        
        # Frecuente: Compra regularmente
        elif freq_per_month >= 0.5:
            segment = "Cliente Frecuente"
            recommendations.append(
                f"📊 Patrón estable: {freq_per_month:.1f} compras/mes. Ticket promedio: S/ {avg_ticket:,.2f}."
            )
            if fav_products:
                recommendations.append(
                    f"🛒 Productos favoritos: {', '.join(fav_products)}. Sugerir productos complementarios."
                )
            recommendations.append(
                "📦 Ofrecer plan de compra recurrente con entrega programada para aumentar retención."
            )
        
        # Ocasional
        else:
            segment = "Cliente Ocasional"
            recommendations.append(
                f"📋 {total_orders} compra(s) registrada(s). Gasto acumulado: S/ {total_spent:,.2f}."
            )
            recommendations.append(
                "🎁 Enviar cupón de incentivo para segunda compra (+15% descuento en pedido > S/ 500)."
            )
            if fav_products:
                recommendations.append(
                    f"💡 Basado en su interés por {fav_products[0]}, sugerir kit complementario."
                )
            recommendations.append(
                "📞 Programar contacto de seguimiento para entender necesidades del negocio."
            )
    
    return {
        "status": "success",
        "message": segment,
        "recommendations": recommendations,
        "metrics": {
            "total_orders": len(orders),
            "total_spent": sum([float(o.total_price) for o in orders]) if orders else 0,
            "avg_ticket": sum([float(o.total_price) for o in orders]) / len(orders) if orders else 0,
            "days_since_last": (datetime.utcnow() - orders[0].created_at).days if orders else None,
            "segment": segment
        }
    }
