import os
import json
import httpx
from pathlib import Path
from typing import Optional, Union
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from google import genai
from google.genai import types
from models import CoinVisionAnalysis, WallapopItem


class VisionArbitrageService:
    def __init__(self, api_key_or_service: Union[str, object] = None, api_key: Optional[str] = None):
        resolved_key = None

        if isinstance(api_key_or_service, str) and api_key_or_service.strip():
            resolved_key = api_key_or_service
        elif api_key and api_key.strip():
            resolved_key = api_key
        elif hasattr(api_key_or_service, "api_key") and getattr(api_key_or_service, "api_key"):
            resolved_key = str(getattr(api_key_or_service, "api_key"))

        if not resolved_key or not isinstance(resolved_key, str) or not resolved_key.strip():
            resolved_key = os.getenv("GEMINI_API_KEY", "").strip()

        if not resolved_key:
            print("[Vision Error] NO se encontró la variable GEMINI_API_KEY en el entorno ni en .env.")

        self.spot_service = api_key_or_service if not isinstance(api_key_or_service, str) else None
        self.client = genai.Client(api_key=resolved_key)

    async def process_item_images(self, item: WallapopItem) -> Optional[CoinVisionAnalysis]:
        if not item.images_hd_urls:
            return None

        model_candidates = ["gemini-2.5-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite"]

        for image_url in item.images_hd_urls:
            try:
                async with httpx.AsyncClient(follow_redirects=True) as http_client:
                    resp = await http_client.get(image_url, timeout=10.0)
                    if resp.status_code != 200 or len(resp.content) < 1000:
                        continue

                    image_bytes = resp.content
                    mime_type = resp.headers.get("content-type", "image/jpeg")

                    prompt = f"""
                    Analiza la imagen adjunta de este anuncio de Wallapop titulado: "{item.titulo}".
                    Identifica la moneda numismática/coleccionable de plata presente en la imagen.

                    Devuelve EXCLUSIVAMENTE un objeto JSON estricto con esta estructura:
                    {{
                        "moneda_detectada": "Nombre específico de la moneda",
                        "peso_g": peso_total_estimado_en_gramos_float,
                        "ley": pureza_de_plata_entre_0_y_1_float,
                        "confianza": nivel_de_confianza_entre_0_y_1_float
                    }}
                    """

                    response = None
                    for model_name in model_candidates:
                        try:
                            response = self.client.models.generate_content(
                                model=model_name,
                                contents=[
                                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                                    prompt,
                                ],
                                config=types.GenerateContentConfig(
                                    response_mime_type="application/json",
                                    temperature=0.1,
                                ),
                            )
                            if response and response.text:
                                break
                        except Exception:
                            continue

                    if response and response.text:
                        data = json.loads(response.text)

                        # Si Gemini devolvió una lista [{...}], tomamos el primer elemento
                        if isinstance(data, list) and len(data) > 0:
                            data = data[0]

                        if isinstance(data, dict):
                            return CoinVisionAnalysis(
                                moneda_detectada=data.get("moneda_detectada", "Moneda Desconocida"),
                                peso_g=float(data.get("peso_g", 0.0)),
                                ley=float(data.get("ley", 0.0)),
                                confianza=float(data.get("confianza", 0.0)),
                            )
            except Exception as e:
                print(f"[Vision Error] Fallo probando imagen en {item.id}: {e}")
                continue

        return None