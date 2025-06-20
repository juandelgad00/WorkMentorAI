# backend/agentes/agente_base.py
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

class AgenteBase:
    """Clase base para todos los agentes, inicializa el LLM de Google Gemini."""
    def __init__(self, model_name="gemini-2.5-flash-lite-preview-06-17", temperature=0.7):
        load_dotenv()
        # Asegúrate de que la API key está cargada
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("La variable de entorno GOOGLE_API_KEY no está configurada.")
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )

    def ejecutar(self, *args, **kwargs):
        raise NotImplementedError("Cada agente debe implementar su propio método 'ejecutar'.")