"""
JHIRE 2026 — Recommendation Use Case (IA Personalization)
==========================================================
Application service that orchestrates the AI-driven recommendation
scoring algorithm. Depends on abstract ports, not infrastructure.

Hexagonal Architecture:
  Domain Ports ← Use Case (RecommendationService) → Presentation (Router)

Scoring Algorithm (0-100):
  - View Frequency:      30%
  - Purchase History:    25%
  - Category Affinity:   25%
  - Recency Bonus:       10%
  - Collaborative:       10%

Dynamic Discount Rules:
  - Persistent Interest: ≥5 views without purchase → 5%
  - Loyalty:             ≥3 completed orders      → 8%
  - Restock:             revisited after 30+ days  → 3%
  - Favorite Category:   ≥40% views in category   → 10%
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple


class RecommendationService:
    """
    Pure business logic for personalized recommendations.
    Receives pre-fetched data — no database dependency.
    """

    # Score weights
    W_FREQUENCY = 30
    W_PURCHASE = 25
    W_AFFINITY = 25
    W_RECENCY = 10
    W_COLLABORATIVE = 10

    @staticmethod
    def compute_category_analytics(
        user_views: list,
        product_map: dict
    ) -> Tuple[dict, int, int, Optional[str]]:
        """
        Analyze user view patterns to determine:
        - category_view_counts: {category: total_views}
        - total_views: sum of all view counts
        - max_views: highest single product view count
        - favorite_category: category with ≥40% of views (or None)
        """
        category_view_counts = {}
        total_views = 0
        max_views = 1

        for v in user_views:
            total_views += v.view_count
            if v.view_count > max_views:
                max_views = v.view_count
            prod = product_map.get(v.product_id)
            if prod and prod.category:
                category_view_counts[prod.category] = (
                    category_view_counts.get(prod.category, 0) + v.view_count
                )

        favorite_category = None
        if total_views > 0:
            for cat, count in category_view_counts.items():
                if count / total_views >= 0.4:
                    favorite_category = cat
                    break

        return category_view_counts, total_views, max_views, favorite_category

    @staticmethod
    def score_product(
        product,
        view_map: dict,
        purchased_ids: set,
        purchased_categories: set,
        category_view_counts: dict,
        total_views: int,
        max_views: int,
        collaborative_ids: set,
        now: datetime
    ) -> Tuple[float, List[str]]:
        """
        Compute a 0-100 relevance score for a single product.
        Returns (score, list_of_reasons).
        """
        score = 0.0
        reasons = []
        pv = view_map.get(product.id)

        # (A) View Frequency — 30%
        if pv:
            freq_score = min((pv.view_count / max_views) * 30, 30)
            score += freq_score
            if pv.view_count >= 3:
                reasons.append(f"Visitaste {pv.view_count}x")

        # (B) Purchase History — 25%
        if product.id in purchased_ids:
            score += 20
            reasons.append("Comprado anteriormente")
        elif product.category and product.category in purchased_categories:
            score += 15
            reasons.append("Categoría que compras")

        # (C) Category Affinity — 25%
        if product.category and product.category in category_view_counts:
            cat_views = category_view_counts[product.category]
            if total_views > 0:
                affinity = (cat_views / total_views) * 25
                score += affinity

        # (D) Recency Bonus — 10%
        if pv and pv.last_viewed:
            hours_since = (now - pv.last_viewed).total_seconds() / 3600
            if hours_since <= 48:
                score += 10
                reasons.append("Visto recientemente")
            elif hours_since <= 168:
                score += 5

        # (E) Collaborative Filtering — 10%
        if product.id in collaborative_ids:
            score += 10
            reasons.append("Otros clientes también compraron")

        return min(score, 100.0), reasons

    @staticmethod
    def compute_discount(
        product,
        view_map: dict,
        purchased_ids: set,
        total_orders: int,
        favorite_category: Optional[str],
        user_orders: list,
        order_items_map: dict,
        now: datetime
    ) -> Tuple[float, Optional[str]]:
        """
        Determine the best dynamic discount for a product.
        Returns (discount_pct, discount_label).
        """
        pv = view_map.get(product.id)
        discount_pct = 0.0
        discount_label = None

        # Rule 1: Persistent Interest — ≥5 views without purchase → 5%
        if pv and pv.view_count >= 5 and product.id not in purchased_ids:
            discount_pct = max(discount_pct, 5.0)
            discount_label = "Interés Persistente"

        # Rule 2: Loyalty — ≥3 completed orders → 8%
        if total_orders >= 3:
            if discount_pct < 8.0:
                discount_pct = 8.0
                discount_label = "Descuento Fidelidad"

        # Rule 3: Restock — revisited purchased product after 30d → 3%
        if product.id in purchased_ids and pv:
            for order in user_orders:
                items = order_items_map.get(order.id, [])
                match = any(it.product_id == product.id for it in items)
                if match:
                    if (now - order.created_at).days >= 30:
                        if discount_pct < 3.0:
                            discount_pct = 3.0
                            discount_label = "Reabastecimiento"
                    break

        # Rule 4: Favorite Category → 10%
        if favorite_category and product.category == favorite_category:
            if discount_pct < 10.0:
                discount_pct = 10.0
                discount_label = "Tu Categoría Favorita"

        return discount_pct, discount_label
