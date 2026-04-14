from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_sales_data():
    return {
        "funnel": {
            "total_value": 1200000,
            "avg_cycle_days": 14,
            "conversion_pct": 7.4
        },
        "quarterly_target": 78,
        "remaining_amount": 240000,
        "recent_activity": [
            {"date": "Oct 24, 14:20", "client": "Global Automotriz S.A.", "type": "Industrial Supply"},
            {"date": "Oct 24, 11:05", "client": "Textiles del Norte", "type": "Manufacturer"},
            {"date": "Oct 23, 16:45", "client": "Logística Integral S.C.", "type": "Warehouse Operations"},
            {"date": "Oct 23, 09:12", "client": "Minería del Pacífico", "type": "Industrial Mining"}
        ],
        "ai_insight": "Historical data suggests an increase in demand for Synthetic Nylon Brushes in the textile sector over the next 15 days. We recommend proactive outreach to Top 5 clients."
    }
