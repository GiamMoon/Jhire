from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ...infrastructure.database import get_db
from ...infrastructure.models import User, ClientProfile, CRMInteraction

router = APIRouter()

@router.get("/clients")
def get_clients(db: Session = Depends(get_db)):
    users = db.query(User).filter(User.role != "admin").all()
    
    clients_data = []
    for u in users:
        profile = db.query(ClientProfile).filter(ClientProfile.user_id == u.id).first()
        interactions = db.query(CRMInteraction).filter(CRMInteraction.user_id == u.id).count()
        
        clients_data.append({
            "id": u.id,
            "name": f"{u.first_name} {u.last_name}",
            "email": u.email,
            "phone": u.phone,
            "company": profile.company_name if profile else "N/A",
            "ruc_dni": profile.ruc_dni if profile else "N/A",
            "interactions_count": interactions,
            "consent_29733": profile.data_protection_consent if profile else False
        })
    return clients_data

@router.get("/clients/{user_id}/interactions")
def get_interactions(user_id: int, db: Session = Depends(get_db)):
    interactions = db.query(CRMInteraction).filter(CRMInteraction.user_id == user_id).order_by(CRMInteraction.date.desc()).all()
    return interactions

@router.get("/recommendations/{user_id}")
def get_recommendations(user_id: int, db: Session = Depends(get_db)):
    from ...infrastructure.models import Order
    orders = db.query(Order).filter(Order.user_id == user_id, Order.status != "Cancelado").all()
    
    if not orders:
        return {
            "status": "success",
            "message": "Nuevos prospectos",
            "recommendations": [
                "El usuario recién se ha registrado. Sugerencia: Enviar oferta B2B del 10% de descuento.",
                "Programar una llamada de bienvenida."
            ]
        }
    
    total_spent = sum([float(o.total_price) for o in orders])
    total_orders = len(orders)
    
    if total_spent > 5000:
        return {
            "status": "success",
            "message": "Cliente VIP",
            "recommendations": [
                f"LTV del cliente alto (S/ {total_spent:.2f}). Sugerir migración a Facturación de Suscripción.",
                "Disparar alerta al equipo Key Account Managers para visita presencial al cliente."
            ]
        }
    else:
        return {
            "status": "success",
            "message": "Cliente Activo",
            "recommendations": [
                f"Tiene {total_orders} pedidos previos. Sugerir productos complementarios de limpieza según su rubro.",
                "Enviar correo automático de re-apastecimiento considerando que ya puede haberse agotado su stock anterior."
            ]
        }
