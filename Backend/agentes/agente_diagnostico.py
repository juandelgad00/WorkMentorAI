# backend/agentes/agente_diagnostico.py
from .agente_base import AgenteBase
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# La estructura de PerfilUsuario se mantiene, es una buena base
class PerfilUsuario(BaseModel):
    nombre: str = Field(description="Nombre completo del candidato.")
    email: str = Field(description="Correo electrónico de contacto.")
    resumen: str = Field(description="Copia literal del resumen profesional o perfil del CV original.")
    habilidades: List[str] = Field(description="Lista de habilidades técnicas y blandas (ej. Python, Liderazgo, Microsoft Office).")
    experiencia: List[Dict[str, Any]] = Field(description="Lista de experiencias laborales con 'cargo', 'empresa', 'periodo' y 'descripcion'.")
    educacion: List[Dict[str, Any]] = Field(description="Lista de estudios realizados con 'titulo', 'institucion' y 'año'.")
    region_colombia: str = Field(description="Ciudad o departamento en Colombia donde reside o busca trabajo. Inferir de la información de contacto.")

class AgenteDiagnostico(AgenteBase):
    
    def ejecutar(self, texto_cv: str, puesto_deseado: str) -> dict:
        print(f"\n🤖 Agente Diagnóstico: Analizando CV para el puesto de '{puesto_deseado}'...")

        # --- PASO 1: EXTRACCIÓN ESTRUCTURADA DE DATOS ---
        parser = JsonOutputParser(pydantic_object=PerfilUsuario)
        # <-- PROMPT DE EXTRACCIÓN REFORZADO -->
        prompt_extraccion = ChatPromptTemplate.from_template(
            "Eres un asistente de RRHH extremadamente preciso y literal. Tu única tarea es analizar el texto de un CV y extraer la información en el formato JSON solicitado. **No infieras ni asumas información; extrae los datos tal como aparecen en el documento.**\n\n"
            "**Instrucciones Específicas para la Extracción:**\n"
            "*   Para la 'experiencia', asegúrate de que el campo 'cargo' contenga el título exacto del puesto (ej. 'Auxiliar en Pedagogía', 'Asesor Comercial') y no un término genérico.\n"
            "*   Para la 'educacion', extrae todos los títulos, incluyendo diplomas, técnicos, tecnólogos y cursos relevantes.\n\n"
            "{format_instructions}\n\n"
            "--- TEXTO DEL CV ---\n{texto_cv}\n--- FIN DEL TEXTO ---"
        )
        cadena_extraccion = prompt_extraccion | self.llm | parser
        
        try:
            perfil_extraido = cadena_extraccion.invoke({
                "texto_cv": texto_cv,
                "format_instructions": parser.get_format_instructions()
            })
        except Exception as e:
            print(f"Error al parsear el perfil del CV: {e}")
            # Devolvemos un error estructurado si falla la extracción
            return {"error": "No se pudo analizar la estructura del CV. Por favor, asegúrate de que el PDF contenga texto seleccionable y un formato estándar."}


        # --- PASO 2: ANÁLISIS PROFUNDO Y GENERACIÓN DE RESUMEN MEJORADO ---
        # Este nuevo prompt es el cerebro de la operación.
        prompt_mejora_integral = ChatPromptTemplate.from_template(
            "Eres un Coach de Carrera y Redactor de Perfiles Profesionales de alto nivel para el mercado colombiano. Tu misión es crear un **'Resumen Profesional Mejorado'** que sintetice de forma impactante toda la información relevante de un candidato.\n\n"
            "**OBJETIVO DEL CANDIDATO:**\n"
            "*   **Puesto Deseado:** {puesto_deseado}\n\n"
            "**DATOS COMPLETOS DEL CV (Tu única fuente de verdad):**\n"
            "*   **Resumen Original:** {resumen_original}\n"
            "*   **Experiencia Laboral Detectada:** {experiencia}\n"
            "*   **Educación Detectada (incluyendo diplomados, técnicos, etc. Sin repetir documentos):** {educacion}\n" # <-- Énfasis en la educación
            "*   **Habilidades Listadas:** {habilidades}\n\n"
            "**INSTRUCCIONES ESTRICTAS:**\n"
            "1.  **Síntesis Integral:** Tu principal tarea es **conectar todos los puntos**. El resumen debe reflejar no solo la experiencia, sino también cómo la **educación formal (incluyendo diplomados y certificaciones)** respalda el perfil del candidato. ¡No omitas la educación relevante!\n"
            "2.  **Fidelidad a los Datos:** Basa tu redacción **ÚNICA Y EXCLUSIVAMENTE** en los datos proporcionados. No inventes experiencia o estudios que no estén listados.\n"
            "3.  **Enfoque en Relevancia:** Relaciona siempre la experiencia y la educación con el **'{puesto_deseado}'**. Si el candidato tiene un 'Diplomado en Innovación Pedagógica' y busca un puesto de ventas, puedes conectar esa habilidad diciendo algo como '...con una capacidad única para educar a los clientes sobre los productos...'.\n"
            "4.  **Estructura del Resumen:**\n"
            "    *   Inicia con una frase potente que defina al profesional.\n"
            "    *   En el cuerpo, **menciona explícitamente su formación más relevante** (ej. '...respaldado/a por un Diplomado en...') y cómo complementa su experiencia práctica.\n"
            "    *   Concluye con su objetivo y propuesta de valor.\n\n"
            "**Resultado Final:** Genera únicamente el texto del **'Resumen Profesional Mejorado'**. Debe ser un párrafo conciso y potente."
        )

        cadena_mejora = prompt_mejora_integral | self.llm | StrOutputParser()
        
        # Invocamos la cadena con todos los datos extraídos
        resumen_mejorado = cadena_mejora.invoke({
            "puesto_deseado": puesto_deseado,
            "resumen_original": perfil_extraido.get('resumen', 'No proporcionado'),
            "experiencia": perfil_extraido.get('experiencia', []),
            "educacion": perfil_extraido.get('educacion', []),
            "habilidades": ", ".join(perfil_extraido.get('habilidades', []))
        })
        
        # Unimos el perfil extraído con el nuevo resumen mejorado
        perfil_completo = perfil_extraido
        perfil_completo['resumen_mejorado'] = resumen_mejorado
        
        print("✅ Diagnóstico y mejora de perfil completados.")
        return perfil_completo