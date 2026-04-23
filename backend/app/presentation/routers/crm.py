from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta

from ...infrastructure.database import get_db
from ...infrastructure.models import User, ClientProfile, CRMInteraction, Order, OrderItem, Product

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
