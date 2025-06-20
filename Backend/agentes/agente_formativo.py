# backend/agentes/agente_formativo.py
from .agente_base import AgenteBase
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field  # Asegúrate de importar de pydantic
from typing import List, Optional
import urllib.parse

# <-- ¡AQUÍ ESTÁ LA PARTE QUE FALTABA! -->
# 1. Definimos las estructuras de datos que el LLM debe generar.
class RecomendacionCurso(BaseModel):
    nombre: str = Field(description="Nombre claro y específico de la recomendación (ej. 'Curso de Cierre de Ventas en YouTube', 'Ruta de Carrera en Platzi').")
    descripcion: str = Field(description="Descripción concisa de por qué es valiosa esta recomendación para el candidato.")
    plataforma_sugerida: Optional[str] = Field(description="La plataforma asociada. Debe ser una de: 'youtube', 'sena', 'coursera', 'platzi', 'edx', o 'blog'.")

class PlanFormativoEstructurado(BaseModel):
    habilidades_clave: List[str] = Field(description="Lista de 2 a 3 habilidades clave que el candidato debe desarrollar.")
    opciones_gratuitas: List[RecomendacionCurso] = Field(description="Lista de recomendaciones de formación gratuitas.")
    opciones_bajo_costo: List[RecomendacionCurso] = Field(description="Lista de recomendaciones de formación de bajo costo.")


class AgenteFormativo(AgenteBase):

    def _generar_link_busqueda(self, plataforma: str, puesto: str) -> str:
        query = urllib.parse.quote_plus(puesto)
        links = {
            'youtube': f"https://www.youtube.com/results?search_query=curso+de+{query}",
            'sena': "https://oferta.senasofiaplus.edu.co/sofia-oferta/buscar-oferta-educativa.html",
            'coursera': f"https://www.coursera.org/search?query={query}",
            'platzi': f"https://platzi.com/search/?q={query}",
            'edx': f"https://www.edx.org/search?q={query}",
            'blog': f"https://www.google.com/search?q=mejores+blogs+de+{query}"
        }
        return links.get(plataforma, "#")

    def ejecutar(self, perfil: dict, puesto_deseado: str) -> dict:
        print(f"\n🤖 Agente Formativo (v-JSON): Creando plan de formación para '{puesto_deseado}'...")
        
        if not puesto_deseado:
            puesto_deseado = perfil.get('habilidades', ['desarrollo profesional'])[0]

        habilidades_actuales = ", ".join(perfil.get('habilidades', ['ninguna especificada']))
        region = perfil.get('region_colombia', 'Colombia')

        # Ahora Python sabrá qué es PlanFormativoEstructurado
        parser = JsonOutputParser(pydantic_object=PlanFormativoEstructurado)

        prompt_json = ChatPromptTemplate.from_template(
            "Eres un orientador vocacional experto en Colombia. Tu tarea es analizar el perfil de un candidato y generar un plan de formación estructurado en formato JSON.\n\n"
            "**Contexto del Candidato:**\n"
            "*   **Objetivo Profesional:** {puesto_deseado}\n"
            "*   **Ubicación:** {region}\n"
            "*   **Habilidades Actuales:** {habilidades_actuales}\n\n"
            "**Instrucciones:**\n"
            "1.  Identifica las 2 o 3 habilidades más importantes que el candidato necesita para el puesto de '{puesto_deseado}'.\n"
            "2.  Genera 2 recomendaciones de formación gratuitas y 1 o 2 de bajo costo. Sé específico con los nombres.\n"
            "3.  Asocia cada recomendación con una plataforma (youtube, sena, coursera, platzi, edx, blog).\n"
            "4.  Devuelve tu respuesta únicamente en el formato JSON solicitado, sin ningún otro texto o explicación.\n\n"
            "{format_instructions}"
        )

        cadena_plan = prompt_json | self.llm | parser
        
        try:
            plan_estructurado = cadena_plan.invoke({
                "puesto_deseado": puesto_deseado,
                "habilidades_actuales": habilidades_actuales,
                "region": region,
                "format_instructions": parser.get_format_instructions()
            })

            print("✅ Plan de formación estructurado generado con éxito.")
            return plan_estructurado

        except Exception as e:
            print(f"Error al generar o parsear el plan formativo: {e}")
            return {"error": "Lo siento, hubo un problema al generar tu plan de formación. Por favor, intenta de nuevo."}