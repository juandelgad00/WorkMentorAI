# backend/utils/cargador_pdf.py
from PyPDF2 import PdfReader
import io

def cargar_texto_cv_desde_stream(stream: io.BytesIO) -> str:
    """Carga y extrae el texto de un stream de bytes de un PDF."""
    try:
        reader = PdfReader(stream)
        texto_completo = "\n".join([page.extract_text() for page in reader.pages])
        return texto_completo
    except Exception as e:
        print(f"Error al cargar el PDF desde el stream: {e}")
        return ""