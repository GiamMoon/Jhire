import os
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

class LLMService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.model_path = None
        return cls._instance

    def _load_model(self):
        if self.model is not None:
            return

        print("Downloading or loading local LLM model... (This may take a minute)")
        self.model_path = hf_hub_download(
            repo_id="Qwen/Qwen2.5-0.5B-Instruct-GGUF",
            filename="qwen2.5-0.5b-instruct-q4_k_m.gguf"
        )
        
        self.model = Llama(
            model_path=self.model_path,
            n_ctx=8192, # Context window
            n_threads=4, # Number of CPU threads
            verbose=False
        )
        print("Local LLM model loaded successfully.")

    def generate_response(self, context: str, user_message: str) -> str:
        self._load_model()
        
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
        
        output = self.model.create_chat_completion(
            messages=messages,
            max_tokens=300,
            temperature=0.3
        )
        
        return output['choices'][0]['message']['content'].strip()

llm_service = LLMService()
