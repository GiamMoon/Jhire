from fastapi import APIRouter, Depends # type: ignore
from sqlalchemy.orm import Session # type: ignore
from datetime import datetime, timedelta
import numpy as np

try:
    from sklearn.ensemble import RandomForestRegressor # type: ignore
    import pandas as pd
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from ...infrastructure.database import get_db
from ...infrastructure.models import Invoice

router = APIRouter()

@router.get("/predict")
def predict_processing_time(db: Session = Depends(get_db)):

    if not SKLEARN_AVAILABLE:
        return {"error": "Scikit-Learn o Pandas no están instalados en el servidor."}
        
    invoices = db.query(Invoice).filter(Invoice.processing_time_seconds > 0).all()
    
    if len(invoices) < 5:
        return {
            "status": "insufficient_data",
            "message": "Se requieren al menos 5 facturas para entrenar el modelo predictivo.",
            "promedio_actual": 0.0,
            "prediccion_30d": []
        }
        
    # Preparar el Dataset
    data = []
    for inv in invoices:
        data.append({
            "weekday": inv.issue_date.weekday(),
            "hour": inv.issue_date.hour,
            "day": inv.issue_date.day,
            "month": inv.issue_date.month,
            "processing_time": inv.processing_time_seconds / 60.0  # en minutos
        })
        
    df = pd.DataFrame(data)
    
    # Feature matrix X y Target y
    X = df[["weekday", "hour", "day", "month"]]
    y = df["processing_time"]
    
    # Entrenar modelo (Random Forest)
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X, y)
    
    # Importancia de Variables
    feature_importances = model.feature_importances_
    importancias = [
        {"feature": "Día de la semana", "importancia": float(feature_importances[0])},
        {"feature": "Hora de cierre", "importancia": float(feature_importances[1])},
        {"feature": "Día del mes", "importancia": float(feature_importances[2])},
        {"feature": "Mes", "importancia": float(feature_importances[3])}
    ]
    
    # Ordenar importancias
    importancias.sort(key=lambda x: x["importancia"], reverse=True)
    
    # Predicción para los próximos 30 días (asumiendo un promedio de horas operativas, ej. 15:00 hrs)
    start_date = datetime.now()
    predicciones = []
    
    for i in range(30):
        target_date = start_date + timedelta(days=i)
        X_pred = pd.DataFrame([{
            "weekday": target_date.weekday(),
            "hour": 15, # Hora pico asumida para el pronóstico
            "day": target_date.day,
            "month": target_date.month
        }])
        
        predicted_time = float(model.predict(X_pred)[0])
        # Agregar algo de ruido al pronóstico para simular variabilidad SUNAT
        ruido = np.random.uniform(-0.01, 0.02)
        predicted_time = max(0.01, predicted_time + ruido)
        
        predicciones.append({
            "fecha": target_date.strftime("%d/%m"),
            "tiempo_predicho_min": round(predicted_time, 2)
        })
        
    # Promedios
    actual_val = round(df["processing_time"].mean(), 2)
    promedio_esperado = round(sum(p["tiempo_predicho_min"] for p in predicciones) / len(predicciones), 2)
    
    # Generar Insight de IA
    diff = actual_val - promedio_esperado
    if actual_val > 0 and diff > 0:
        mejora_pct = (diff / actual_val) * 100
        insight = f"El motor IA predice una tendencia a la baja en tiempos de SUNAT (-{mejora_pct:.1f}%). La facturación automática se mantendrá eficiente, rondando los {promedio_esperado} minutos por comprobante."
    elif actual_val > 0 and diff < 0:
        empeora_pct = abs(diff / actual_val) * 100
        insight = f"¡Alerta! El modelo detecta que los próximos días podrían presentar un incremento del {empeora_pct:.1f}% en la latencia de SUNAT, principalmente los {importancias[0]['feature']}. Se priorizará el envío encolado."
    else:
        insight = f"El sistema es estable. Se proyecta mantener el procesamiento en {promedio_esperado} minutos por factura."

    return {
        "status": "success",
        "prediccion_30d": predicciones,
        "importancia_features": importancias,
        "promedio_actual": actual_val,
        "promedio_esperado": promedio_esperado,
        "modelo": "Random Forest Regressor (Optimizador SUNAT)",
        "insight_texto": insight
    }
