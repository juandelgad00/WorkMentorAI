# backend/agentes/agente_conector.py
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

class AgenteConector:

    def _scrape_linkedin(self, puesto: str, location: str) -> List[Dict[str, str]]:
        print(f"... Scrapeando LinkedIn para '{puesto}' en '{location}'")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            query_encoded = urllib.parse.quote_plus(puesto)
            location_encoded = urllib.parse.quote_plus(f"{location}, Colombia")
            url = f"https://co.linkedin.com/jobs/search?keywords={query_encoded}&location={location_encoded}&f_TPR=r604800&position=1&pageNum=0"
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            ofertas = []
            job_cards = soup.find_all('div', class_='base-card')

            for card in job_cards:
                if len(ofertas) >= 5:
                    break
                title_tag = card.find('h3', class_='base-search-card__title')
                company_tag = card.find('h4', class_='base-search-card__subtitle')
                link_tag = card.find('a', class_='base-card__full-link')

                if title_tag and company_tag and link_tag and link_tag.get('href') and '******' not in title_tag.get_text():
                    ofertas.append({
                        "puesto": title_tag.get_text(strip=True),
                        "empresa": company_tag.get_text(strip=True),
                        "link": link_tag['href']
                    })
            
            print(f"... Encontradas {len(ofertas)} ofertas válidas en LinkedIn.")
            return ofertas
            
        except requests.exceptions.RequestException as e:
            print(f"Error al scrapear LinkedIn: {e}")
            return [{"puesto": "Error al buscar en LinkedIn", "empresa": str(e), "link": "#"}]

    def _generar_link_computrabajo(self, puesto: str, location: str) -> List[Dict[str, str]]:
        print(f"... Generando enlace de búsqueda para CompuTrabajo para '{puesto}' en '{location}'")
        try:
            # --- LÓGICA DE CONSTRUCCIÓN DE URL CORREGIDA ---

            # 1. Normalizar y convertir a formato "slug" (separado por guiones)
            puesto_slug = puesto.strip().lower().replace(" ", "-")
            
            # Para la ubicación, CompuTrabajo suele usar solo la ciudad principal.
            # Tomamos la primera parte antes de la coma.
            ciudad_principal = location.split(',')[0].strip()
            location_slug = ciudad_principal.lower().replace(" ", "-").replace(".", "")
            
            # Eliminamos tildes y caracteres especiales para mayor compatibilidad
            import unicodedata
            def normalizar_texto(texto):
                return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

            puesto_slug = normalizar_texto(puesto_slug)
            location_slug = normalizar_texto(location_slug)

            # 2. Construir la URL final con el formato correcto
            url = f"https://www.computrabajo.com.co/trabajo-de-{puesto_slug}-en-{location_slug}"
            
            print(f"... URL generada para CompuTrabajo: {url}")

            return [{
                "puesto": f"Ver ofertas para '{puesto}' en CompuTrabajo",
                "empresa": "Haz clic para ver la lista de empleos",
                "link": url
            }]
        except Exception as e:
            print(f"Error al generar link de CompuTrabajo: {e}")
            return [{"puesto": "Error al generar link de CompuTrabajo", "empresa": str(e), "link": "#"}]


    def ejecutar(self, perfil: dict, puesto_deseado: str) -> dict:
        print("\n🤖 Agente Conector (v-Síncrona Estable): Buscando ofertas...")
        
        if not puesto_deseado:
            puesto_deseado = perfil.get('habilidades', ['empleo'])[0]

        region = perfil.get('region_colombia', 'Colombia')
        
        # Hacemos las llamadas una después de la otra. Simple y efectivo.
        ofertas_linkedin = self._scrape_linkedin(puesto_deseado, region)
        link_computrabajo = self._generar_link_computrabajo(puesto_deseado, region)
        
        print("✅ Búsqueda de ofertas completada.")
        return {
            "linkedin": ofertas_linkedin,
            "computrabajo": link_computrabajo
        }