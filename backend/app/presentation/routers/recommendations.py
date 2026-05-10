"""
JHIRE 2026 — Personalized Recommendations Engine
=================================================
Algoritmo de scoring 0-100 basado en:
  - Frecuencia de vistas (30%)
  - Historial de compras (25%)
  - Afinidad de categoría (25%)
  - Bonus de recencia (10%)
  - Complementarios (10%)

Descuentos dinámicos automáticos:
  - Interés Persistente: ≥5 vistas sin compra → 5%
  - Fidelidad: ≥3 órdenes completadas → 8%
  - Reabastecimiento: re-visitó producto comprado >30d → 3%
  - Categoría Favorita: ≥60% de vistas en una categoría → 10% en esa categoría
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ...infrastructure.database import get_db
from ...infrastructure.models import (
    User, Product, ProductView, Order, OrderItem
)
from ...infrastructure.security import get_current_user

router = APIRouter()

# =====================================================
# SCHEMAS
# =====================================================

class TrackViewRequest(BaseModel):
    product_id: int

class RecommendedProduct(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price_soles: float
    image_url: Optional[str] = None
    stock: int
    category: Optional[str] = None
    score: float = 0.0
    reason: str = ""
    discount_pct: float = 0.0
    discount_label: Optional[str] = None
    discounted_price: Optional[float] = None

    class Config:
        from_attributes = True

class PersonalDiscount(BaseModel):
    product_id: int
    product_name: str
    image_url: Optional[str] = None
    original_price: float
    discount_pct: float
    discount_label: str
    discounted_price: float
    reason: str

class RecommendationResponse(BaseModel):
    recommended: List[RecommendedProduct]
    personal_discounts: List[PersonalDiscount]
    user_profile: dict


# =====================================================
# ENDPOINT: TRACK PRODUCT VIEW
# =====================================================

@router.post("/track-view")
def track_product_view(
    req: TrackViewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registra o incrementa la vista de un producto para el usuario autenticado."""
    product = db.query(Product).filter(Product.id == req.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    existing = db.query(ProductView).filter(
        ProductView.user_id == current_user.id,
        ProductView.product_id == req.product_id
    ).first()

    if existing:
        existing.view_count += 1
        existing.last_viewed = datetime.utcnow()
    else:
        new_view = ProductView(
            user_id=current_user.id,
            product_id=req.product_id,
            view_count=1,
            first_viewed=datetime.utcnow(),
            last_viewed=datetime.utcnow()
        )
        db.add(new_view)

    db.commit()
    return {"status": "tracked", "product_id": req.product_id}


# =====================================================
# ENDPOINT: PERSONALIZED RECOMMENDATIONS
# =====================================================

@router.get("/for-me", response_model=RecommendationResponse)
def get_personalized_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Motor de recomendación personalizada.
    Retorna productos rankeados por scoring + descuentos dinámicos.
    """
    user_id = current_user.id
    now = datetime.utcnow()

    # ─── GATHER USER DATA ───────────────────────────────
    # 1. All user product views
    user_views = db.query(ProductView).filter(
        ProductView.user_id == user_id
    ).all()

    # 2. All products the user has purchased
    purchased_product_ids = set()
    purchased_categories = set()
    user_orders = db.query(Order).filter(
        Order.user_id == user_id,
        Order.status != "Cancelado"
    ).all()
    total_orders = len(user_orders)

    for order in user_orders:
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        for item in items:
            purchased_product_ids.add(item.product_id)
            prod = db.query(Product).filter(Product.id == item.product_id).first()
            if prod and prod.category:
                purchased_categories.add(prod.category)

    # 3. View frequency analytics
    view_map = {}  # product_id -> ProductView
    category_view_counts = {}  # category -> total views
    total_views = 0
    max_views = 1

    for v in user_views:
        view_map[v.product_id] = v
        total_views += v.view_count
        if v.view_count > max_views:
            max_views = v.view_count
        prod = db.query(Product).filter(Product.id == v.product_id).first()
        if prod and prod.category:
            category_view_counts[prod.category] = category_view_counts.get(prod.category, 0) + v.view_count

    # 4. Determine favorite category (≥60% of views)
    favorite_category = None
    if total_views > 0:
        for cat, count in category_view_counts.items():
            if count / total_views >= 0.4:  # 40% threshold (adjusted for small catalogs)
                favorite_category = cat
                break

    # 5. Collaborative: products bought by users who bought same products
    collaborative_ids = set()
    if purchased_product_ids:
        # Find other users who bought the same products
        similar_users = db.query(OrderItem.order_id).join(Order).filter(
            OrderItem.product_id.in_(purchased_product_ids),
            Order.user_id != user_id,
            Order.status != "Cancelado"
        ).distinct().all()
        similar_order_ids = [s[0] for s in similar_users]

        if similar_order_ids:
            collab_items = db.query(OrderItem.product_id).filter(
                OrderItem.order_id.in_(similar_order_ids),
                ~OrderItem.product_id.in_(purchased_product_ids)
            ).distinct().limit(10).all()
            collaborative_ids = {c[0] for c in collab_items}

    # ─── SCORE ALL PRODUCTS ─────────────────────────────
    all_products = db.query(Product).filter(Product.stock > 0).all()
    scored_products = []

    for product in all_products:
        score = 0.0
        reasons = []

        # (A) View Frequency Score — 30% weight
        pv = view_map.get(product.id)
        if pv:
            freq_score = min((pv.view_count / max_views) * 30, 30)
            score += freq_score
            if pv.view_count >= 3:
                reasons.append(f"Visitaste {pv.view_count}x")

        # (B) Purchase History Score — 25% weight
        if product.id in purchased_product_ids:
            score += 20  # Bought before → high relevance but cap at 20 (save 5 for restock)
            reasons.append("Comprado anteriormente")
        elif product.category and product.category in purchased_categories:
            score += 15  # Same category as purchased items
            reasons.append("Categoría que compras")

        # (C) Category Affinity Score — 25% weight
        if product.category and product.category in category_view_counts:
            cat_views = category_view_counts[product.category]
            if total_views > 0:
                affinity = (cat_views / total_views) * 25
                score += affinity

        # (D) Recency Bonus — 10% weight
        if pv and pv.last_viewed:
            hours_since = (now - pv.last_viewed).total_seconds() / 3600
            if hours_since <= 48:
                score += 10
                reasons.append("Visto recientemente")
            elif hours_since <= 168:  # 1 week
                score += 5

        # (E) Collaborative Filtering — 10% weight
        if product.id in collaborative_ids:
            score += 10
            reasons.append("Otros clientes también compraron")

        # Clamp score
        score = min(score, 100.0)

        # ─── DYNAMIC DISCOUNTS ──────────────────────────
        discount_pct = 0.0
        discount_label = None

        # Rule 1: Persistent Interest — viewed ≥5x without buying → 5%
        if pv and pv.view_count >= 5 and product.id not in purchased_product_ids:
            discount_pct = max(discount_pct, 5.0)
            discount_label = "Interés Persistente"

        # Rule 2: Loyalty — ≥3 completed orders → 8% on all
        if total_orders >= 3:
            if discount_pct < 8.0:
                discount_pct = 8.0
                discount_label = "Descuento Fidelidad"

        # Rule 3: Restock — revisited a purchased product after 30d → 3%
        if product.id in purchased_product_ids and pv:
            last_purchase = None
            for order in user_orders:
                items = db.query(OrderItem).filter(
                    OrderItem.order_id == order.id,
                    OrderItem.product_id == product.id
                ).first()
                if items:
                    last_purchase = order.created_at
                    break
            if last_purchase and (now - last_purchase).days >= 30:
                if discount_pct < 3.0:
                    discount_pct = 3.0
                    discount_label = "Reabastecimiento"

        # Rule 4: Favorite Category — ≥60% views in one category → 10%
        if favorite_category and product.category == favorite_category:
            if discount_pct < 10.0:
                discount_pct = 10.0
                discount_label = "Tu Categoría Favorita"

        discounted_price = round(product.price_soles * (1 - discount_pct / 100), 2) if discount_pct > 0 else None

        reason_text = " · ".join(reasons) if reasons else "Producto popular"

        scored_products.append(RecommendedProduct(
            id=product.id,
            name=product.name,
            description=product.description,
            price_soles=product.price_soles,
            image_url=product.image_url,
            stock=product.stock,
            category=product.category,
            score=round(score, 1),
            reason=reason_text,
            discount_pct=discount_pct,
            discount_label=discount_label,
            discounted_price=discounted_price
        ))

    # Sort by score descending
    scored_products.sort(key=lambda x: x.score, reverse=True)

    # ─── PERSONAL DISCOUNTS LIST ────────────────────────
    personal_discounts = []
    for sp in scored_products:
        if sp.discount_pct > 0:
            personal_discounts.append(PersonalDiscount(
                product_id=sp.id,
                product_name=sp.name,
                image_url=sp.image_url,
                original_price=sp.price_soles,
                discount_pct=sp.discount_pct,
                discount_label=sp.discount_label or "",
                discounted_price=sp.discounted_price or sp.price_soles,
                reason=sp.reason
            ))

    # ─── USER PROFILE SUMMARY ───────────────────────────
    user_profile = {
        "total_views": total_views,
        "unique_products_viewed": len(user_views),
        "total_orders": total_orders,
        "favorite_category": favorite_category,
        "categories_viewed": dict(category_view_counts),
        "purchased_product_count": len(purchased_product_ids)
    }

    return RecommendationResponse(
        recommended=scored_products[:12],  # Top 12
        personal_discounts=personal_discounts[:6],  # Top 6 discounts
        user_profile=user_profile
    )


# =====================================================
# ENDPOINT: PERSONAL DISCOUNTS ONLY
# =====================================================

@router.get("/discounts")
def get_personal_discounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns only the personalized discount offers for the current user."""
    full = get_personalized_recommendations(db=db, current_user=current_user)
    return {
        "discounts": [d.dict() for d in full.personal_discounts],
        "count": len(full.personal_discounts)
    }


# =====================================================
# ENDPOINT: TRENDING PRODUCTS (no auth required)
# =====================================================

@router.get("/trending")
def get_trending_products(db: Session = Depends(get_db)):
    """
    Returns globally trending products based on:
    - Total view count across all users
    - Recent purchase velocity
    """
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    # Most viewed products (last 7 days)
    trending_views = db.query(
        ProductView.product_id,
        func.sum(ProductView.view_count).label("total_views")
    ).filter(
        ProductView.last_viewed >= week_ago
    ).group_by(
        ProductView.product_id
    ).order_by(
        desc("total_views")
    ).limit(8).all()

    trending_ids = [t[0] for t in trending_views]
    view_scores = {t[0]: t[1] for t in trending_views}

    # If not enough trending data, fill with most purchased
    if len(trending_ids) < 8:
        recent_purchases = db.query(
            OrderItem.product_id,
            func.sum(OrderItem.quantity).label("total_qty")
        ).join(Order).filter(
            Order.created_at >= week_ago,
            Order.status != "Cancelado"
        ).group_by(
            OrderItem.product_id
        ).order_by(
            desc("total_qty")
        ).limit(8 - len(trending_ids)).all()

        for rp in recent_purchases:
            if rp[0] not in trending_ids:
                trending_ids.append(rp[0])
                view_scores[rp[0]] = rp[1]

    # If still not enough, add random products with stock
    if len(trending_ids) < 4:
        fillers = db.query(Product).filter(
            Product.stock > 0,
            ~Product.id.in_(trending_ids) if trending_ids else True
        ).limit(4 - len(trending_ids)).all()
        for f in fillers:
            trending_ids.append(f.id)
            view_scores[f.id] = 0

    products = db.query(Product).filter(Product.id.in_(trending_ids)).all()

    result = []
    for p in products:
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price_soles": p.price_soles,
            "image_url": p.image_url,
            "stock": p.stock,
            "category": p.category,
            "trending_score": view_scores.get(p.id, 0),
            "label": "🔥 Trending"
        })

    result.sort(key=lambda x: x["trending_score"], reverse=True)
    return result


# =====================================================
# ENDPOINT: COMPLEMENTARY PRODUCTS
# =====================================================

@router.get("/complementary/{product_id}")
def get_complementary_products(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Returns products complementary to a given product, based on:
    1. Same category (but different product)
    2. Co-purchased products (bought together in same orders)
    3. Price-range peers
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    complementary = []
    seen_ids = {product_id}

    # 1. Co-purchased: products in orders that also contain this product
    orders_with_product = db.query(OrderItem.order_id).filter(
        OrderItem.product_id == product_id
    ).all()
    order_ids = [o[0] for o in orders_with_product]

    if order_ids:
        co_purchased = db.query(
            OrderItem.product_id,
            func.count(OrderItem.id).label("freq")
        ).filter(
            OrderItem.order_id.in_(order_ids),
            OrderItem.product_id != product_id
        ).group_by(
            OrderItem.product_id
        ).order_by(
            desc("freq")
        ).limit(4).all()

        for cp in co_purchased:
            if cp[0] not in seen_ids:
                p = db.query(Product).filter(Product.id == cp[0], Product.stock > 0).first()
                if p:
                    complementary.append({
                        "id": p.id, "name": p.name, "description": p.description,
                        "price_soles": p.price_soles, "image_url": p.image_url,
                        "stock": p.stock, "category": p.category,
                        "reason": "Comprados juntos frecuentemente"
                    })
                    seen_ids.add(p.id)

    # 2. Same category
    if product.category:
        same_cat = db.query(Product).filter(
            Product.category == product.category,
            Product.id != product_id,
            Product.stock > 0,
            ~Product.id.in_(seen_ids) if seen_ids else True
        ).limit(4 - len(complementary)).all()

        for sc in same_cat:
            if sc.id not in seen_ids:
                complementary.append({
                    "id": sc.id, "name": sc.name, "description": sc.description,
                    "price_soles": sc.price_soles, "image_url": sc.image_url,
                    "stock": sc.stock, "category": sc.category,
                    "reason": "Misma categoría"
                })
                seen_ids.add(sc.id)

    # 3. Price-range peers (±30%)
    if len(complementary) < 4:
        price_low = product.price_soles * 0.7
        price_high = product.price_soles * 1.3
        price_peers = db.query(Product).filter(
            Product.price_soles.between(price_low, price_high),
            Product.id != product_id,
            Product.stock > 0,
            ~Product.id.in_(seen_ids) if seen_ids else True
        ).limit(4 - len(complementary)).all()

        for pp in price_peers:
            if pp.id not in seen_ids:
                complementary.append({
                    "id": pp.id, "name": pp.name, "description": pp.description,
                    "price_soles": pp.price_soles, "image_url": pp.image_url,
                    "stock": pp.stock, "category": pp.category,
                    "reason": "Rango de precio similar"
                })
                seen_ids.add(pp.id)

    return complementary[:4]


# =====================================================
# ENDPOINT: USER VIEW HISTORY
# =====================================================

@router.get("/my-history")
def get_my_view_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns the user's product view history sorted by most recent."""
    views = db.query(ProductView).filter(
        ProductView.user_id == current_user.id
    ).order_by(desc(ProductView.last_viewed)).limit(20).all()

    result = []
    for v in views:
        product = db.query(Product).filter(Product.id == v.product_id).first()
        if product:
            result.append({
                "product_id": v.product_id,
                "product_name": product.name,
                "image_url": product.image_url,
                "price_soles": product.price_soles,
                "view_count": v.view_count,
                "last_viewed": v.last_viewed.isoformat(),
                "first_viewed": v.first_viewed.isoformat()
            })

    return result
