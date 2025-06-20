# backend/main.py
import os
import io
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Form
from pydantic import BaseModel
from typing import Dict, Any

# Importaciones de nuestros módulos
from utils.cargador_pdf import cargar_texto_cv_desde_stream
from agentes.agente_diagnostico import AgenteDiagnostico
from agentes.agente_formativo import AgenteFormativo
from agentes.agente_creativo import AgenteCreativo
from agentes.agente_conector import AgenteConector
from agentes.agente_simulador import AgenteSimulador
from agentes.agente_mentor import AgenteMentor

# Crear directorios si no existen
os.makedirs("cv_uploads", exist_ok=True)

app = FastAPI(
    title="Sistema Multiagente de Empleabilidad Juvenil CO",
    description="Una API para potenciar la carrera de jóvenes en Colombia mediante IA Generativa.",
    version="1.0.0"
)

# Configuración de CORS para permitir que el frontend se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las origenes, ajusta en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instanciamos los agentes una sola vez
agentes = {
    "diagnostico": AgenteDiagnostico(),
    "formativo": AgenteFormativo(),
    "creativo": AgenteCreativo(),
    "conector": AgenteConector(),
    "simulador": AgenteSimulador(model_name="gemini-2.5-flash-lite-preview-06-17"), # Usamos el modelo base para chat
    "mentor": AgenteMentor()
}

# --- Modelos de Datos para las Peticiones (Request Bodies) ---
class PerfilUsuarioRequest(BaseModel):
    perfil: Dict[str, Any]

class CartaRequest(BaseModel):
    perfil: Dict[str, Any]
    puesto_deseado: str

# En backend/main.py

# ... (Definición de ChatRequest)
class ChatRequest(BaseModel):
    perfil: Dict[str, Any]
    puesto_deseado: str 
    historial: list # Ahora esta será la única fuente de la conversación
    # mensaje_actual ya no es necesario aquí

@app.post("/diagnosticar_cv/", summary="Agente 1: Diagnostica un CV")
async def diagnosticar_cv(
    puesto_deseado: str = Form(...), # Recibimos el puesto desde el formulario
    file: UploadFile = File(...)
):
    """
    Recibe un CV en PDF y el puesto deseado. Analiza el perfil y devuelve
    un análisis estructurado y un resumen profesional mejorado.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF.")
    
    try:
        # ... (código para guardar y leer el archivo no cambia)
        contents = await file.read()
        texto_cv = cargar_texto_cv_desde_stream(io.BytesIO(contents))
        if not texto_cv:
            raise HTTPException(status_code=500, detail="No se pudo extraer texto del PDF.")
        
        # <-- Pasamos el 'puesto_deseado' al agente -->
        perfil = agentes["diagnostico"].ejecutar(texto_cv, puesto_deseado)
        return perfil
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocurrió un error en el servidor: {e}")


@app.post("/recomendar_formacion/", summary="Agente 2: Recomienda un Plan Formativo")
async def recomendar_formacion(request: CartaRequest): # Usamos CartaRequest para tener perfil y puesto
    """
    Basado en un perfil de usuario, genera un plan de formación personalizado en formato JSON.
    """
    plan_json = agentes["formativo"].ejecutar(request.perfil, request.puesto_deseado)
    return plan_json

@app.post("/generar_carta/", summary="Agente 3: Crea una Carta de Presentación")
async def generar_carta(request: CartaRequest):
    """
    Crea una carta de presentación en español e inglés, y la evalúa.
    """
    artefactos = agentes["creativo"].ejecutar(request.perfil, request.puesto_deseado)
    return artefactos

@app.post("/buscar_ofertas/", summary="Agente 4: Conecta con Ofertas Laborales")
async def buscar_ofertas(request: CartaRequest):
    """
    Busca enlaces a ofertas laborales en portales colombianos usando el puesto deseado.
    """
    # <-- ¡CAMBIO IMPORTANTE! Se ha quitado 'await' -->
    ofertas = agentes["conector"].ejecutar(request.perfil, request.puesto_deseado)
    return ofertas


@app.post("/chat/simulador/", summary="Agente 5: Simula una Entrevista")
async def chat_simulador(request: ChatRequest):
    """
    Endpoint conversacional para la simulación de entrevistas.
    Maneja el historial de la conversación.
    """
    # <-- CAMBIO: Pasamos un solo argumento con todo el historial
    respuesta = agentes["simulador"].ejecutar_paso(
        perfil=request.perfil,
        puesto_deseado=request.puesto_deseado,
        historial_completo=request.historial 
    )
    return {"respuesta_agente": respuesta}

@app.post("/chat/mentor/", summary="Agente 6: Proporciona Mentoría")
async def chat_mentor(request: ChatRequest):
    """
    Endpoint conversacional para el agente mentor.
    """
    # Modificamos la llamada para que sea consistente
    respuesta = agentes["mentor"].ejecutar_paso(
        perfil=request.perfil,
        historial_completo=request.historial
    )
    return {"respuesta_agente": respuesta}

# Para que esto funcione, necesitas modificar ligeramente los agentes simulador y mentor
# para que acepten el historial y el mensaje actual como parámetros en un método `ejecutar_paso`.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)