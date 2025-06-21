# Importación de librerías estándar y de terceros necesarias para la API
import os
import io
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

# Importación de módulos internos del proyecto (utilidades y agentes)
from utils.cargador_pdf import cargar_texto_cv_desde_stream
from agentes.agente_diagnostico import AgenteDiagnostico
from agentes.agente_formativo import AgenteFormativo
from agentes.agente_creativo import AgenteCreativo
from agentes.agente_conector import AgenteConector
from agentes.agente_simulador import AgenteSimulador
from agentes.agente_mentor import AgenteMentor

# Crear carpeta para almacenar CVs si no existe
os.makedirs("cv_uploads", exist_ok=True)

# Inicialización de la aplicación FastAPI con metadatos descriptivos
app = FastAPI(
    title="Sistema Multiagente de Empleabilidad Juvenil CO",
    description="Una API para potenciar la carrera de jóvenes en Colombia mediante IA Generativa.",
    version="1.0.0"
)

# Configuración de CORS para permitir acceso desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicialización de instancias de agentes IA especializados (se cargan una sola vez)
agentes = {
    "diagnostico": AgenteDiagnostico(),
    "formativo": AgenteFormativo(),
    "creativo": AgenteCreativo(),
    "conector": AgenteConector(),
    "simulador": AgenteSimulador(model_name="gemini-2.5-flash-lite-preview-06-17"),
    "mentor": AgenteMentor()
}

# Modelos de datos para solicitudes HTTP
class PerfilUsuarioRequest(BaseModel):
    perfil: Dict[str, Any]

class CartaRequest(BaseModel):
    perfil: Dict[str, Any]
    puesto_deseado: str

class ChatRequest(BaseModel):
    perfil: Dict[str, Any]
    puesto_deseado: str 
    historial: list

# ---------- Endpoints de los Agentes ----------

@app.post("/diagnosticar_cv/", summary="Agente 1: Diagnostica un CV")
async def diagnosticar_cv(puesto_deseado: str = Form(...), file: UploadFile = File(...)):
    """
    Recibe un CV en PDF y un puesto deseado. Devuelve un diagnóstico del perfil
    profesional y un resumen mejorado.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF.")
    
    try:
        contents = await file.read()
        texto_cv = cargar_texto_cv_desde_stream(io.BytesIO(contents))
        if not texto_cv:
            raise HTTPException(status_code=500, detail="No se pudo extraer texto del PDF.")
        
        perfil = agentes["diagnostico"].ejecutar(texto_cv, puesto_deseado)
        return perfil
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocurrió un error en el servidor: {e}")

@app.post("/recomendar_formacion/", summary="Agente 2: Recomienda un Plan Formativo")
async def recomendar_formacion(request: CartaRequest):
    """
    Genera una ruta de formación personalizada basada en el perfil del usuario y su aspiración.
    """
    plan_json = agentes["formativo"].ejecutar(request.perfil, request.puesto_deseado)
    return plan_json

@app.post("/generar_carta/", summary="Agente 3: Crea una Carta de Presentación")
async def generar_carta(request: CartaRequest):
    """
    Genera una carta de presentación profesional en español e inglés, junto con su evaluación.
    """
    artefactos = agentes["creativo"].ejecutar(request.perfil, request.puesto_deseado)
    return artefactos

@app.post("/buscar_ofertas/", summary="Agente 4: Conecta con Ofertas Laborales")
async def buscar_ofertas(request: CartaRequest):
    """
    Busca ofertas laborales en portales como LinkedIn y Computrabajo con base en la región y puesto deseado.
    """
    ofertas = agentes["conector"].ejecutar(request.perfil, request.puesto_deseado)
    return ofertas

@app.post("/chat/simulador/", summary="Agente 5: Simula una Entrevista")
async def chat_simulador(request: ChatRequest):
    """
    Simula una entrevista de trabajo en formato conversacional, con retroalimentación posterior.
    """
    respuesta = agentes["simulador"].ejecutar_paso(
        perfil=request.perfil,
        puesto_deseado=request.puesto_deseado,
        historial_completo=request.historial 
    )
    return {"respuesta_agente": respuesta}

@app.post("/chat/mentor/", summary="Agente 6: Proporciona Mentoría")
async def chat_mentor(request: ChatRequest):
    """
    Proporciona acompañamiento emocional y responde dudas del usuario relacionadas con su búsqueda laboral.
    """
    respuesta = agentes["mentor"].ejecutar_paso(
        perfil=request.perfil,
        historial_completo=request.historial
    )
    return {"respuesta_agente": respuesta}

# Punto de entrada de la aplicación
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
