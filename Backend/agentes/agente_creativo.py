# backend/agentes/agente_creativo.py
from .agente_base import AgenteBase
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from pydantic import BaseModel, Field
from typing import List

# 1. Definimos la estructura de datos que queremos para el análisis de idoneidad
class AnalisisIdoneidad(BaseModel):
    calificacion_habilidades: int = Field(description="Calificación de 1 a 10 sobre qué tan bien las habilidades del candidato se alinean con el puesto deseado.")
    calificacion_experiencia: int = Field(description="Calificación de 1 a 10 sobre la relevancia de la experiencia del candidato para el puesto. Si no hay experiencia, la calificación debe ser baja.")
    calificacion_estudios: int = Field(description="Calificación de 1 a 10 sobre la relevancia de los estudios del candidato para el puesto.")
    puntos_fuertes: List[str] = Field(description="Lista de 2 o 3 puntos fuertes clave del candidato para este puesto específico.")
    puntos_debiles: List[str] = Field(description="Lista de 2 o 3 debilidades o áreas de mejora evidentes para este puesto.")
    sugerencias_mejora: List[str] = Field(description="Lista de 2 sugerencias concretas y accionables para que el candidato mejore su perfil para este puesto.")

class AgenteCreativo(AgenteBase):

    def _analizar_idoneidad(self, perfil: dict, puesto_deseado: str) -> dict:
        """
        Analiza el perfil del candidato en comparación con el puesto deseado y devuelve un análisis estructurado.
        """
        print(f"...[Analista] Comparando perfil con el puesto de '{puesto_deseado}'...")
        
        parser = JsonOutputParser(pydantic_object=AnalisisIdoneidad)
        
        prompt_analisis = ChatPromptTemplate.from_template(
            "Eres un 'Analista de Talento y Reclutador Senior' para el mercado colombiano. Tu tarea es realizar un análisis de idoneidad (fit-gap analysis) comparando el perfil de un candidato con un puesto de trabajo deseado. Debes ser objetivo, crítico y constructivo.\n\n"
            "**PUESTO OBJETIVO:** {puesto_deseado}\n\n"
            "**PERFIL DEL CANDIDATO:**\n"
            "*   **Experiencia:** {experiencia}\n"
            "*   **Educación:** {educacion}\n"
            "*   **Habilidades:** {habilidades}\n\n"
            "**INSTRUCCIONES:**\n"
            "1.  **Califica cada área (habilidades, experiencia, estudios) de 1 a 10**, donde 10 es un encaje perfecto. Sé realista; si no hay experiencia relevante, la calificación debe ser baja (1-3).\n"
            "2.  **Identifica los Puntos Fuertes:** ¿Qué hace que este candidato destaque para este rol?\n"
            "3.  **Identifica los Puntos Débiles:** ¿Cuáles son las brechas más grandes entre su perfil y los requisitos del puesto?\n"
            "4.  **Ofrece Sugerencias Accionables:** Proporciona dos consejos concretos que el candidato podría seguir para cerrar esas brechas (ej. 'Obtener una certificación en X', 'Realizar un proyecto personal para demostrar Y').\n"
            "5.  Devuelve tu análisis estrictamente en el formato JSON solicitado.\n\n"
            "{format_instructions}"
        )
        
        cadena_analisis = prompt_analisis | self.llm | parser
        
        analisis = cadena_analisis.invoke({
            "puesto_deseado": puesto_deseado,
            "experiencia": perfil.get('experiencia', 'No especificada'),
            "educacion": perfil.get('educacion', 'No especificada'),
            "habilidades": ", ".join(perfil.get('habilidades', [])),
            "format_instructions": parser.get_format_instructions()
        })
        
        return analisis

    def _generar_carta_ejemplo(self, perfil: dict, puesto_deseado: str, analisis: dict) -> dict:
        """
        Genera una carta de presentación de ejemplo (ES y EN) dirigida a una empresa ficticia,
        resaltando los puntos fuertes identificados en el análisis.
        """
        print("...[Creativo] Generando carta de presentación de ejemplo...")

        # Prompt para la carta en español
        prompt_carta_es = ChatPromptTemplate.from_template(
            "Eres un escritor de documentos de carrera. Tu tarea es redactar una carta de presentación de ejemplo, profesional y persuasiva, para el puesto de **'{puesto_deseado}'**. La carta debe estar dirigida a una empresa colombiana ficticia pero realista (ej. 'TecnoSoluciones Andinas S.A.S.', 'Logística Colombo-Global').\n\n"
            "**Usa esta información para personalizar la carta:**\n"
            "*   **Nombre del Candidato:** {nombre}\n"
            "*   **Puntos Fuertes Clave (a resaltar en la carta):** {puntos_fuertes}\n"
            "*   **Resumen del Perfil:** {resumen_mejorado}\n\n"
            "**Estructura de la Carta:**\n"
            "1.  **Encabezado:** Fecha, Nombre del Candidato, Contacto.\n"
            "2.  **Destinatario:** 'Equipo de Recursos Humanos', [Nombre de la Empresa Ficticia], [Ciudad, Colombia].\n"
            "3.  **Párrafo 1 (Introducción):** Expresa el interés en el puesto de '{puesto_deseado}'.\n"
            "4.  **Párrafo 2 (Cuerpo):** Conecta los **puntos fuertes** identificados con las necesidades del puesto. Este es el párrafo más importante.\n"
            "5.  **Párrafo 3 (Cierre):** Reitera el entusiasmo y llama a la acción (solicitar una entrevista).\n"
            "6.  **Despedida:** 'Atentamente,', [Nombre del Candidato].\n\n"
            "Genera únicamente el texto completo de la carta en español."
        )
        cadena_carta_es = prompt_carta_es | self.llm | StrOutputParser()
        carta_es = cadena_carta_es.invoke({
            "puesto_deseado": puesto_deseado,
            "nombre": perfil.get('nombre', 'El/La Candidato/a'),
            "puntos_fuertes": ", ".join(analisis.get('puntos_fuertes', [])),
            "resumen_mejorado": perfil.get('resumen_mejorado', '')
        })

        # Traducción al inglés
        prompt_traduccion = ChatPromptTemplate.from_template(
            "You are a professional translator. Your task is to translate the following cover letter into natural, professional American English. Maintain the same structure and tone.\n\n"
            "**Spanish Text:**\n{texto_a_traducir}\n\n"
            "**English Translation:**"
        )
        cadena_traduccion = prompt_traduccion | self.llm | StrOutputParser()
        carta_en = cadena_traduccion.invoke({"texto_a_traducir": carta_es})
        
        return {"carta_es": carta_es, "carta_en": carta_en}


    def ejecutar(self, perfil: dict, puesto_deseado: str) -> dict:
        print("\n🤖 Agente Creativo (Analista de Idoneidad): Iniciando proceso...")
        
        # 1. Realizar el análisis de idoneidad
        analisis_idoneidad = self._analizar_idoneidad(perfil, puesto_deseado)
        
        # 2. Generar las cartas de ejemplo basadas en el análisis
        cartas_ejemplo = self._generar_carta_ejemplo(perfil, puesto_deseado, analisis_idoneidad)
        
        # 3. Unir todos los resultados en un solo objeto
        resultado_final = {
            "analisis_idoneidad": analisis_idoneidad,
            "cartas_ejemplo": cartas_ejemplo
        }
        
        print("✅ Análisis y artefactos creativos generados con éxito.")
        return resultado_final