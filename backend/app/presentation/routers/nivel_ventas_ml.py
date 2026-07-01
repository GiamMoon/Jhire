from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ...infrastructure.database import get_db
from ...infrastructure.models import Order
from datetime import datetime, timedelta, date
import numpy as np

router = APIRouter()



def calcular_pcv(vr: float, va: float) -> float:
    if va <= 0:
        return 0.0
    return round(((vr / va) - 1) * 100, 2)


def _ventas_diarias(db: Session) -> dict:
    """Retorna {date: total_soles} de todas las órdenes no canceladas."""
    orders = (
        db.query(Order)
        .filter(Order.status != "Cancelado")
        .order_by(Order.created_at)
        .all()
    )
    daily: dict[date, float] = {}
    for o in orders:
        d = o.created_at.date()
        daily[d] = daily.get(d, 0.0) + float(o.total_price)
    return daily


def _rellenar_dias(daily: dict) -> dict:
    """Rellena días sin ventas con 0 para tener una serie continua."""
    if not daily:
        return daily
    sorted_dates = sorted(daily.keys())
    cur = sorted_dates[0]
    while cur <= sorted_dates[-1]:
        daily.setdefault(cur, 0.0)
        cur += timedelta(days=1)
    return daily


def _construir_dataset(sorted_dates: list, daily: dict):

    X, y = [], []
    for i in range(7, len(sorted_dates)):
        d = sorted_dates[i]
        window = [daily.get(sorted_dates[j], 0.0) for j in range(i - 7, i)]
        X.append([
            i,
            float(np.mean(window)),
            float(np.std(window)) if np.std(window) > 0 else 0.01,
            d.weekday(),
            d.month,
            daily.get(sorted_dates[i - 1], 0.0),
            daily.get(sorted_dates[i - 7], 0.0),
            float(np.sum(window)),
        ])
        y.append(daily.get(d, 0.0))
    return np.array(X), np.array(y)



@router.get("/pcv")
def get_pcv_actual(db: Session = Depends(get_db)):
    """
    Calcula el PCV real mes a mes con órdenes de la BD.
    Retorna la serie mensual de los últimos 6 meses.
    """
    now = datetime.utcnow()
    serie = []

    for delta in range(5, -1, -1):
        # Mes actual del slice
        mes_ref = (now.replace(day=1) - timedelta(days=delta * 28)).replace(day=1)
        mes_sig = (mes_ref + timedelta(days=32)).replace(day=1)
        mes_ant = (mes_ref - timedelta(days=1)).replace(day=1)

        vr = db.query(func.sum(Order.total_price)).filter(
            Order.status != "Cancelado",
            Order.created_at >= mes_ref,
            Order.created_at < mes_sig,
        ).scalar() or 0.0

        va = db.query(func.sum(Order.total_price)).filter(
            Order.status != "Cancelado",
            Order.created_at >= mes_ant,
            Order.created_at < mes_ref,
        ).scalar() or 0.0

        serie.append({
            "mes": mes_ref.strftime("%b %Y"),
            "VR": round(float(vr), 2),
            "VA": round(float(va), 2),
            "PCV": calcular_pcv(float(vr), float(va)),
        })

    actual = serie[-1]
    return {
        "formula": "PCV = [(VR / VA) - 1] × 100",
        "fuente": "Gamboa & Villarreal, 2021",
        "mes_actual": actual["mes"],
        "VR": actual["VR"],
        "VA": actual["VA"],
        "PCV_actual": actual["PCV"],
        "serie_6_meses": serie,
    }



@router.get("/pcv-ml")
def get_pcv_con_ml(db: Session = Depends(get_db)):

    try:
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor # type: ignore
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score # type: ignore
    except ImportError:
        return {"error": "scikit-learn no instalado. Ejecuta: pip install scikit-learn"}

    daily = _rellenar_dias(_ventas_diarias(db))
    if len(daily) < 15:
        return {
            "error": "Datos insuficientes",
            "mensaje": f"Se necesitan ≥15 días de datos. Hay {len(daily)} días disponibles.",
        }

    sorted_dates = sorted(daily.keys())
    X, y = _construir_dataset(sorted_dates, daily)

    if len(X) < 10:
        return {"error": "No hay suficientes muestras para entrenar el modelo."}

    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    rf = RandomForestRegressor(n_estimators=150, max_depth=8,
                               min_samples_leaf=2, random_state=42)
    rf.fit(X_train, y_train)

    gb = GradientBoostingRegressor(n_estimators=150, learning_rate=0.08,
                                   max_depth=4, random_state=42)
    gb.fit(X_train, y_train)

    y_pred_test = 0.6 * rf.predict(X_test) + 0.4 * gb.predict(X_test)
    mae  = round(float(mean_absolute_error(y_test, y_pred_test)), 2)
    rmse = round(float(np.sqrt(mean_squared_error(y_test, y_pred_test))), 2)
    r2   = round(float(r2_score(y_test, y_pred_test)), 4)
    mape = round(
        float(np.mean(np.abs((y_test - y_pred_test) / np.where(y_test == 0, 1, y_test)))) * 100,
        2,
    )

    running = dict(daily)
    running_dates = list(sorted_dates)
    predicciones = []

    for i in range(30):
        future_date = sorted_dates[-1] + timedelta(days=i + 1)
        window = [running.get(running_dates[-(7 - j)], 0.0) for j in range(7)]
        feat = np.array([[
            len(running_dates),
            float(np.mean(window)),
            float(np.std(window)) if np.std(window) > 0 else 0.01,
            future_date.weekday(),
            future_date.month,
            running.get(running_dates[-1], 0.0),
            running.get(running_dates[-7] if len(running_dates) >= 7 else running_dates[0], 0.0),
            float(np.sum(window)),
        ]])
        pred = max(0.0, float(0.6 * rf.predict(feat)[0] + 0.4 * gb.predict(feat)[0]))
        predicciones.append({
            "fecha": future_date.strftime("%Y-%m-%d"),
            "label": future_date.strftime("%d/%m"),
            "VR_dia_predicho": round(pred, 2),
        })
        running[future_date] = pred
        running_dates.append(future_date)

    VA_real = sum(daily.get(d, 0.0) for d in sorted_dates[-30:])

    VR_predicho = sum(p["VR_dia_predicho"] for p in predicciones)

    PCV_predicho = calcular_pcv(VR_predicho, VA_real)

    VA_anterior = sum(daily.get(d, 0.0) for d in sorted_dates[-60:-30]) if len(sorted_dates) >= 60 else VA_real * 0.9
    PCV_actual_sin_ml = calcular_pcv(VA_real, VA_anterior)

    nombres_features = [
        "Índice temporal", "Media 7 días", "Volatilidad 7 días",
        "Día de semana", "Mes del año", "Lag-1 (ayer)", "Lag-7 (semana pasada)",
        "Suma acumulada 7d",
    ]
    importancia = sorted(
        [{"feature": n, "importancia": round(float(v), 4)}
         for n, v in zip(nombres_features, rf.feature_importances_)],
        key=lambda x: x["importancia"],
        reverse=True,
    )

    historico = [
        {"fecha": d.strftime("%d/%m"), "VR_real": round(daily.get(d, 0.0), 2)}
        for d in sorted_dates[-30:]
    ]

    return {

        # ── Valores para la fórmula
        "VA_real_30d":        round(VA_real, 2),
        "VR_predicho_30d":    round(VR_predicho, 2),
        "PCV_predicho_ml":    PCV_predicho,
        "PCV_actual_sin_ml":  PCV_actual_sin_ml,

        # ── Interpretación
        "interpretacion": (
            f"El modelo ML predice VR = S/ {VR_predicho:,.2f} para los próximos 30 días. "
            f"Con VA = S/ {VA_real:,.2f} (período anterior real), "
            f"el PCV predicho es {PCV_predicho:+.2f}%. "
            f"Sin ML el PCV actual era {PCV_actual_sin_ml:+.2f}%."
        ),

        # ── Calidad del modelo
        "modelo": {
            "algoritmo": "Random Forest (60%) + Gradient Boosting (40%) — Ensamble",
            "MAE_soles": mae,
            "RMSE_soles": rmse,
            "R2": r2,
            "MAPE_pct": mape,
            "precision_pct": round(max(0.0, 100.0 - mape), 1),
            "muestras_entrenamiento": int(len(X_train)),
            "muestras_prueba":        int(len(X_test)),
        },

        # ── Features más importantes
        "importancia_features": importancia,

        # ── Datos para gráficas
        "historico_30d":     historico,
        "prediccion_30d":    predicciones,
    }


@router.get("/ficha-diaria")
def get_ficha_diaria(
    start_date: str = None, 
    end_date: str = None, 
    db: Session = Depends(get_db)
):

    daily = _ventas_diarias(db)
    if not daily:
        return {"data": [], "promedio_crecimiento_periodo": 0}
    
    daily = _rellenar_dias(daily)
    sorted_dates = sorted(daily.keys())
    
    if start_date:
        start_d = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        start_d = sorted_dates[-30] if len(sorted_dates) >= 30 else sorted_dates[0]
        
    if end_date:
        end_d = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        end_d = sorted_dates[-1]
        
    current = start_d
    results = []
    item = 1
    
    while current <= end_d:
        vr = daily.get(current, 0.0)
        # VA = ventas del día equivalente, 30 días antes
        ref_date = current - timedelta(days=30)
        va = daily.get(ref_date, 0.0)
        
        if va > 0:
            pcv = round(((vr / va) - 1) * 100)
        else:
            pcv = 0
            
        results.append({
            "idx": item,
            "fecha": current.strftime("%d/%m/%Y"),
            "ventas_dia": round(vr, 2),
            "ventas_ayer": round(va, 2),
            "crecimiento": pcv
        })
        
        current += timedelta(days=1)
        item += 1
        
    avg = sum(r["crecimiento"] for r in results) / len(results) if results else 0
        
    return {
        "data": results,
        "promedio_crecimiento_periodo": round(avg, 2)
    }

