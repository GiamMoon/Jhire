"""
JHIRE 2026 — Servicio de LLM Local (Chatbot con IA Generativa)
================================================================
TESIS: Sistema Web para la Gestión Comercial de la Empresa JHIRE

╔══════════════════════════════════════════════════════════════════════════╗
║  MÓDULO DE INTELIGENCIA ARTIFICIAL — CHATBOT CON MODELO DE LENGUAJE   ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  MODELO: Qwen2.5-0.5B-Instruct (formato GGUF cuantizado Q4_K_M)     ║
║                                                                        ║
║  ¿QUÉ ES UN LLM (Large Language Model)?                              ║
║  → Un modelo de inteligencia artificial entrenado en grandes           ║
║    volúmenes de texto para generar respuestas en lenguaje natural.    ║
║  → Qwen2.5-0.5B es un modelo ligero de Alibaba Cloud, optimizado     ║
║    para correr en CPU (no requiere GPU).                              ║
║                                                                        ║
║  ¿POR QUÉ UN LLM LOCAL Y NO UNA API COMO OPENAI/CHATGPT?            ║
║  ──────────────────────────────────────────────────────────────        ║
║  1. PRIVACIDAD DE DATOS:                                              ║
║     → Los datos del catálogo y clientes NO salen del servidor.        ║
║     → Cumple con la Ley N° 29733 de Protección de Datos Personales.  ║
║                                                                        ║
║  2. COSTO CERO:                                                       ║
║     → No hay costos por token/consulta como con OpenAI API.           ║
║     → Una PYME no puede asumir US$20-100/mes en API de IA.            ║
║                                                                        ║
║  3. DISPONIBILIDAD:                                                   ║
║     → No depende de servicios externos ni conexión a internet         ║
║       (una vez descargado el modelo).                                 ║
║     → Sin latencia de red adicional.                                  ║
║                                                                        ║
║  4. PERSONALIZACIÓN:                                                  ║
║     → El prompt del sistema se configura para que SOLO recomiende     ║
║       productos del catálogo real de JHIRE.                           ║
║     → No inventa productos ni precios (anti-alucinación).             ║
║                                                                        ║
║  PATRÓN DE DISEÑO: Singleton                                         ║
║  → Solo se carga UNA instancia del modelo en memoria.                ║
║  → Si se creara una nueva instancia por cada request, el servidor    ║
║    consumiría GBs de RAM innecesariamente.                           ║
║                                                                        ║
║  CUANTIZACIÓN GGUF Q4_K_M:                                           ║
║  → El modelo original pesa ~1GB en FP16.                             ║
║  → Cuantizado a 4 bits pesa ~300MB con pérdida mínima de calidad.    ║
║  → Permite correr en CPUs de computadoras normales.                  ║
║  → Referencia: llama.cpp (Georgi Gerganov, 2023)                     ║
║                                                                        ║
║  UBICACIÓN EN LA ARQUITECTURA:                                        ║
║  → Capa: Domain/Services — Lógica de negocio de IA                   ║
║  → No depende de HTTP ni FastAPI (puede usarse desde cualquier capa)  ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import os
from huggingface_hub import hf_hub_download
from llama_cpp import Llama


class LLMService:
    """
    Servicio de IA Generativa para el Chatbot de Ventas de JHIRE.
    
    PATRÓN SINGLETON:
    ─────────────────
    Se implementa con __new__ para garantizar que solo exista UNA
    instancia del modelo en memoria. El modelo Qwen2.5 consume ~400MB
    de RAM; crear múltiples instancias saturaría el servidor.
    
    ¿POR QUÉ __new__ Y NO UN DECORADOR @singleton?
    → __new__ es el método estándar de Python para controlar la creación
      de instancias. Es más explícito y thread-safe que un decorador.
    """
    _instance = None  # Referencia a la instancia única (Singleton)

    def __new__(cls):
        """
        Controla la creación de instancias (Patrón Singleton).
        Si ya existe una instancia, retorna la misma.
        Si no existe, crea una nueva y la almacena en _instance.
        """
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
            cls._instance.model = None       # Se carga lazy (bajo demanda)
            cls._instance.model_path = None   # Ruta al archivo GGUF descargado
        return cls._instance

    def _load_model(self):
        """
        Carga Lazy del modelo LLM (solo se ejecuta la primera vez).
        
        LAZY LOADING:
        → El modelo NO se carga al iniciar el servidor.
        → Se carga la primera vez que un usuario envía un mensaje al chat.
        → Esto evita que el startup del servidor tarde 30+ segundos.
        
        Proceso:
        1. Descarga el modelo desde Hugging Face Hub (o lo usa del cache)
        2. Carga el modelo con llama-cpp-python (binding de C++ para Python)
        3. Configura context window de 8192 tokens
        """
        if self.model is not None:
            return  # Ya está cargado, no hacer nada

        print("Downloading or loading local LLM model... (This may take a minute)")
        
        # ── Descarga del modelo desde Hugging Face ──────────────────
        # repo_id: repositorio del modelo en Hugging Face
        # filename: archivo GGUF específico (cuantización Q4_K_M)
        # Si ya está en cache (~/.cache/huggingface/), no re-descarga.
        self.model_path = hf_hub_download(
            repo_id="Qwen/Qwen2.5-0.5B-Instruct-GGUF",
            filename="qwen2.5-0.5b-instruct-q4_k_m.gguf"
        )
        
        # ── Carga del modelo en memoria ─────────────────────────────
        # n_ctx=8192 : Context window (cuántos tokens puede procesar)
        #   → 8192 es suficiente para el catálogo de JHIRE + conversación
        # n_threads=4 : Hilos de CPU para inferencia paralela
        #   → Configurado para un servidor con 4 cores mínimo
        # verbose=False : Suprime logs internos de llama.cpp
        self.model = Llama(
            model_path=self.model_path,
            n_ctx=8192,
            n_threads=4,
            verbose=False
        )
        print("Local LLM model loaded successfully.")

    def generate_response(self, context: str, user_message: str) -> str:
        """
        Genera una respuesta del chatbot usando el modelo LLM local.
        
        TÉCNICA: Retrieval-Augmented Generation (RAG simplificado)
        ─────────────────────────────────────────────────────────────
        En vez de entrenar el modelo con datos de JHIRE (fine-tuning),
        se usa la técnica de RAG:
        1. Se RECUPERAN los productos del catálogo desde la BD
        2. Se INYECTAN en el prompt del sistema como contexto
        3. El modelo GENERA respuestas basadas SOLO en ese contexto
        
        Ventaja sobre fine-tuning:
        → El catálogo se actualiza en tiempo real (cada consulta trae
          datos frescos de la BD)
        → No requiere re-entrenar el modelo cuando cambian precios/stock
        
        ANTI-ALUCINACIÓN:
        → El prompt del sistema incluye reglas estrictas:
          "NUNCA inventes nombres de productos que no estén en el CATÁLOGO"
        → Esto minimiza las alucinaciones del modelo (un problema conocido
          de los LLMs).
        
        Args:
            context: Catálogo de productos formateado como texto
            user_message: Pregunta del usuario
        
        Returns:
            str: Respuesta generada por el modelo en español
        """
        self._load_model()  # Carga lazy si es la primera vez
        
        # ── Construcción del prompt con técnica RAG ─────────────────
        # El prompt del sistema define:
        # 1. ROL: Asistente de ventas de JHIRE
        # 2. IDIOMA: Solo español
        # 3. REGLAS ANTI-ALUCINACIÓN: no inventar productos
        # 4. CONTEXTO: catálogo real de la BD como "fuente de verdad"
        messages = [
            {
                "role": "system",
                "content": (
                    "Eres un asistente de ventas de Inteligencia Artificial estricto para JHIRE. "
                    "DEBES escribir ÚNICAMENTE EN ESPAÑOL.\n"
                    "REGLAS CRÍTICAS:\n"
                    "1. NUNCA inventes nombres de productos, enlaces, descripciones ni precios que no estén exactamente en el CATÁLOGO proporcionado. Prohibido alucinar nombres de productos.\n"
                    "2. Si recomiendas un producto del catálogo, SIEMPRE extrae y entrega el 'Link de compra' que aparece en ese exacto producto.\n"
                    "3. Si el usuario pide algo que NO ESTÁ EXPLÍCITAMENTE EN EL CATÁLOGO, dile directamente que NO cuentas con dicho producto.\n"
                    "CATÁLOGO DE PRODUCTOS RECOPILADO (TU ÚNICA FUENTE DE VERDAD):\n"
                    f"{context}"
                )
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
        
        # ── Inferencia del modelo ───────────────────────────────────
        # max_tokens=300 : Limita la respuesta a ~300 tokens (~200 palabras)
        #   → Respuestas concisas, adecuadas para un chat de ventas
        # temperature=0.3 : Baja creatividad → respuestas más factuales
        #   → 0.0 = determinístico (siempre la misma respuesta)
        #   → 1.0 = muy creativo (riesgo de alucinaciones)
        #   → 0.3 = equilibrio entre variedad y precisión
        output = self.model.create_chat_completion(
            messages=messages,
            max_tokens=300,
            temperature=0.3
        )
        
        return output['choices'][0]['message']['content'].strip()


# ═══════════════════════════════════════════════════════════════════════
# INSTANCIA SINGLETON GLOBAL
# ═══════════════════════════════════════════════════════════════════════
# Se crea una instancia global que será importada por el router chat.py.
# Gracias al patrón Singleton, todas las importaciones comparten la
# misma instancia y el mismo modelo cargado en memoria.
llm_service = LLMService()
