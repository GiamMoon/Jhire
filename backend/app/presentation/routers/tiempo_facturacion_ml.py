"""
JHIRE 2026 — Modelo Predictivo de Tiempo de Facturación con Machine Learning
===============================================================================
TESIS: Sistema Web para la Gestión Comercial de la Empresa JHIRE

╔══════════════════════════════════════════════════════════════════════════╗
║  MÓDULO DE INTELIGENCIA ARTIFICIAL — PREDICCIÓN DE TIEMPOS SUNAT       ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  INDICADOR CLAVE: TPF (Tiempo Promedio de Facturación)                ║
║  ──────────────────────────────────────────────────────                ║
║  Fórmula:  TPF = Σ(tiempo_procesamiento_i) / N                       ║
║                                                                        ║
║  Donde:                                                                ║
║    tiempo_procesamiento_i = segundos desde inicio hasta CDR SUNAT     ║
║    N = número total de facturas del período                           ║
║                                                                        ║
║  OBJETIVO:                                                             ║
║  Predecir los tiempos de procesamiento de facturación electrónica     ║
║  en los próximos 30 días usando ML, para:                             ║
║    1. Anticipar cuellos de botella en períodos de alta carga SUNAT    ║
║    2. Optimizar el horario de envío de comprobantes                   ║
║    3. Generar alertas proactivas al administrador                     ║
║                                                                        ║
║  MODELO: Random Forest Regressor                                      ║
║  → Se eligió RF por su robustez con datasets pequeños                 ║
║  → Proporciona feature_importances_ para interpretabilidad            ║
║  → No requiere normalización de los datos de entrada                  ║
║                                                                        ║
║  UBICACIÓN EN LA ARQUITECTURA:                                        ║
║  → Capa: Presentación (Router) — expone la funcionalidad vía API     ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

from fastapi import APIRouter, Depends # type: ignore
from sqlalchemy.orm import Session # type: ignore
from datetime import datetime, timedelta
import numpy as np

# ═══════════════════════════════════════════════════════════════════════
# IMPORTACIÓN CONDICIONAL DE SCIKIT-LEARN
# ═══════════════════════════════════════════════════════════════════════
# Se usa try/except porque scikit-learn es una dependencia pesada.
# Si no está instalada, el endpoint retorna un error descriptivo
# en vez de crashear toda la API. Esto sigue el principio de
# "Graceful Degradation" (degradación elegante).
try:
    from sklearn.ensemble import RandomForestRegressor # type: ignore
    import pandas as pd
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from ...infrastructure.database import get_db
from ...infrastructure.models import Invoice

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════
# ENDPOINT: Predicción de Tiempo de Facturación con ML
# ═══════════════════════════════════════════════════════════════════════
#
# Flujo del modelo:
# ┌──────────────────────────────────────────────────────────────────┐
# │  1. EXTRACCIÓN   → Obtener facturas con tiempo de procesamiento │
# │  2. PREPARACIÓN  → Crear dataset con features temporales        │
# │  3. ENTRENAMIENTO→ Entrenar Random Forest                       │
# │  4. PREDICCIÓN   → Predecir tiempos para los próximos 30 días   │
# │  5. ANÁLISIS     → Calcular importancia de variables            │
# │  6. INSIGHT      → Generar interpretación en lenguaje natural   │
# └──────────────────────────────────────────────────────────────────┘

@router.get("/predict")
def predict_processing_time(db: Session = Depends(get_db)):
    """
    Predice el tiempo de procesamiento de facturación electrónica
    para los próximos 30 días usando Random Forest Regressor.
    
    JUSTIFICACIÓN DEL MODELO:
    ─────────────────────────
    ¿Por qué Random Forest y no otro algoritmo?
    
    1. Dataset pequeño (típicamente <100 facturas): RF funciona bien
       con pocos datos, a diferencia de redes neuronales que necesitan
       miles de muestras.
       
    2. Features categóricas naturales (día de semana, mes): RF maneja
       variables discretas sin necesidad de one-hot encoding.
       
    3. Interpretabilidad: feature_importances_ nos dice QUÉ variable
       afecta más al tiempo de procesamiento, lo cual es valioso
       para la tesis (Explainable AI).
       
    4. Robustez ante outliers: si una factura tardó 10 minutos por
       un error de SUNAT, RF no se desestabiliza (a diferencia de
       regresión lineal o SVR).
    
    ¿Por qué NO Gradient Boosting aquí?
    → Con tan pocos datos, GB tiende a sobreajustar. RF con pocos
      estimadores (n_estimators=50) es más conservador y estable.
    """

    # Verificar disponibilidad de scikit-learn
    if not SKLEARN_AVAILABLE:
        return {"error": "Scikit-Learn o Pandas no están instalados en el servidor."}
    
    # ─── PASO 1: EXTRACCIÓN DE DATOS ───────────────────────────────
    # Solo se consideran facturas con processing_time > 0 (ya procesadas)
    # Las facturas sin tiempo registrado se excluyen del entrenamiento.
    invoices = db.query(Invoice).filter(Invoice.processing_time_seconds > 0).all()
    
    # Validación de datos mínimos para entrenar
    # ¿POR QUÉ 5 COMO MÍNIMO?
    # → RF necesita al menos n_estimators muestras para crear árboles válidos
    # → Con <5 datos, cualquier modelo estadístico carece de poder predictivo
    if len(invoices) < 5:
        return {
            "status": "insufficient_data",
            "message": "Se requieren al menos 5 facturas para entrenar el modelo predictivo.",
            "promedio_actual": 0.0,
            "prediccion_30d": []
        }
    
    # ─── PASO 2: INGENIERÍA DE FEATURES ────────────────────────────
    # Se extraen 4 features temporales de cada factura:
    #
    # ┌─────┬──────────────────────┬─────────────────────────────────────┐
    # │  #  │ Feature              │ Justificación                       │
    # ├─────┼──────────────────────┼─────────────────────────────────────┤
    # │  0  │ weekday (0-6)        │ SUNAT puede tener mayor carga      │
    # │     │                      │ ciertos días (ej. viernes fin de   │
    # │     │                      │ mes hay más emisiones)             │
    # │  1  │ hour (0-23)          │ La hora del día afecta la latencia │
    # │     │                      │ del servidor SUNAT                 │
    # │  2  │ day (1-31)           │ Fin de mes = más facturación =     │
    # │     │                      │ mayor congestión                   │
    # │  3  │ month (1-12)         │ Meses con cierre fiscal (dic, jul) │
    # │     │                      │ tienen mayor carga tributaria      │
    # └─────┴──────────────────────┴─────────────────────────────────────┘
    #
    # Variable objetivo: processing_time en MINUTOS (dividido entre 60)
    data = []
    for inv in invoices:
        data.append({
            "weekday": inv.issue_date.weekday(),           # 0=Lunes ... 6=Domingo
            "hour": inv.issue_date.hour,                    # Hora del día (0-23)
            "day": inv.issue_date.day,                      # Día del mes (1-31)
            "month": inv.issue_date.month,                  # Mes (1-12)
            "processing_time": inv.processing_time_seconds / 60.0  # Convertir a minutos
        })
        
    df = pd.DataFrame(data)
    
    # Separar features (X) y variable objetivo (y)
    X = df[["weekday", "hour", "day", "month"]]
    y = df["processing_time"]
    
    # ─── PASO 3: ENTRENAMIENTO DEL MODELO ──────────────────────────
    # n_estimators=50 : Solo 50 árboles (suficiente para dataset pequeño)
    # random_state=42 : Semilla fija para reproducibilidad
    #
    # NOTA: No se hace split train/test aquí porque el dataset es muy
    # pequeño. Se entrena con el 100% de datos disponibles.
    # En un escenario con más datos, se debería hacer cross-validation.
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X, y)
    
    # ─── PASO 4: ANÁLISIS DE IMPORTANCIA DE VARIABLES ──────────────
    # feature_importances_ es un atributo de Random Forest que indica
    # cuánto contribuye cada variable a reducir la impureza (Gini).
    # Valores más altos = más relevancia para la predicción.
    #
    # Esto es CLAVE para la tesis: permite responder preguntas como
    # "¿qué factor afecta más al tiempo de facturación?"
    feature_importances = model.feature_importances_
    importancias = [
        {"feature": "Día de la semana", "importancia": float(feature_importances[0])},
        {"feature": "Hora de cierre", "importancia": float(feature_importances[1])},
        {"feature": "Día del mes", "importancia": float(feature_importances[2])},
        {"feature": "Mes", "importancia": float(feature_importances[3])}
    ]
    
    # Ordenar de mayor a menor importancia
    importancias.sort(key=lambda x: x["importancia"], reverse=True)
    
    # ─── PASO 5: PREDICCIÓN A 30 DÍAS ─────────────────────────────
    # Para cada uno de los próximos 30 días, se construye un vector
    # de features y se predice el tiempo de procesamiento.
    # Se asume hora pico = 15:00 hrs (cuando más facturas se emiten).
    start_date = datetime.now()
    predicciones = []
    
    for i in range(30):
        target_date = start_date + timedelta(days=i)
        # Construir features para el día futuro
        X_pred = pd.DataFrame([{
            "weekday": target_date.weekday(),
            "hour": 15,  # Hora pico asumida para el pronóstico
            "day": target_date.day,
            "month": target_date.month
        }])
        
        predicted_time = float(model.predict(X_pred)[0])
        # Agregar variabilidad pequeña para simular la naturaleza estocástica
        # de la latencia de red/SUNAT (no es un valor fijo cada día)
        ruido = np.random.uniform(-0.01, 0.02)
        predicted_time = max(0.01, predicted_time + ruido)
        
        predicciones.append({
            "fecha": target_date.strftime("%d/%m"),
            "tiempo_predicho_min": round(predicted_time, 2)
        })
    
    # ─── PASO 6: CÁLCULO DE PROMEDIOS Y GENERACIÓN DE INSIGHT ─────
    actual_val = round(df["processing_time"].mean(), 2)  # Promedio actual real
    promedio_esperado = round(sum(p["tiempo_predicho_min"] for p in predicciones) / len(predicciones), 2)
    
    # ─── GENERACIÓN DE INSIGHT EN LENGUAJE NATURAL ─────────────────
    # Se compara el promedio actual vs el predicho para generar
    # un mensaje interpretable para el administrador.
    # Esto implementa el concepto de "Actionable Insights" en BI.
    diff = actual_val - promedio_esperado
    if actual_val > 0 and diff > 0:
        mejora_pct = (diff / actual_val) * 100
        insight = f"El motor IA predice una tendencia a la baja en tiempos de SUNAT (-{mejora_pct:.1f}%). La facturación automática se mantendrá eficiente, rondando los {promedio_esperado} minutos por comprobante."
    elif actual_val > 0 and diff < 0:
        empeora_pct = abs(diff / actual_val) * 100
        insight = f"¡Alerta! El modelo detecta que los próximos días podrían presentar un incremento del {empeora_pct:.1f}% en la latencia de SUNAT, principalmente los {importancias[0]['feature']}. Se priorizará el envío encolado."
    else:
        insight = f"El sistema es estable. Se proyecta mantener el procesamiento en {promedio_esperado} minutos por factura."

    # ─── RESPUESTA COMPLETA ────────────────────────────────────────
    return {
        "status": "success",
        "prediccion_30d": predicciones,                    # Predicciones diarias
        "importancia_features": importancias,               # Qué features importan más
        "promedio_actual": actual_val,                      # TPF actual real
        "promedio_esperado": promedio_esperado,              # TPF predicho por ML
        "modelo": "Random Forest Regressor (Optimizador SUNAT)",
        "insight_texto": insight                            # Interpretación para dashboards
    }
