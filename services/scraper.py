import re
import json
import asyncio
from typing import List
from playwright.async_api import async_playwright
from models import WallapopItem


class WallapopScraper:
    async def search_items(self, query: str) -> List[WallapopItem]:
        encoded_query = query.replace(" ", "+")
        url = f"https://es.wallapop.com/search?keywords={encoded_query}&order_by=newest"

        print(f"[*] Iniciando búsqueda Fase 1 para: '{query}'...")
        print(f"[*] Navegando a Wallapop e interceptando API GraphQL/JSON...")

        items: List[WallapopItem] = []
        seen_ids = set()
        raw_items_captured = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()

            # Listener de respuestas JSON internas de Wallapop
            async def handle_response(response):
                try:
                    if any(k in response.url for k in ["search", "item", "graphql", "quickstart"]):
                        if "application/json" in response.headers.get("content-type", ""):
                            json_data = await response.json()
                            
                            def extract_objects(obj):
                                if isinstance(obj, dict):
                                    if "searchObjects" in obj and isinstance(obj["searchObjects"], list):
                                        raw_items_captured.extend(obj["searchObjects"])
                                    if "items" in obj and isinstance(obj["items"], list):
                                        raw_items_captured.extend(obj["items"])
                                    for v in obj.values():
                                        extract_objects(v)
                                elif isinstance(obj, list):
                                    for elem in obj:
                                        extract_objects(elem)

                            extract_objects(json_data)
                except Exception:
                    pass

            page.on("response", handle_response)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.evaluate("window.scrollBy(0, 1500)")
                await page.wait_for_timeout(3000)

                # Procesar elementos capturados en red
                for obj in raw_items_captured:
                    if not isinstance(obj, dict):
                        continue

                    item_id = str(obj.get("id", ""))
                    if not item_id or item_id in seen_ids:
                        continue

                    title = obj.get("title", "").strip()
                    
                    # Extracción exacta de Precio
                    price = 0.0
                    price_info = obj.get("price")
                    if isinstance(price_info, dict):
                        price = float(price_info.get("amount", 0.0))
                    elif isinstance(price_info, (int, float)):
                        price = float(price_info)

                    web_slug = obj.get("webSlug", "")
                    item_url = f"https://es.wallapop.com/item/{web_slug}" if web_slug else f"https://es.wallapop.com/item/{item_id}"

                    # Extracción profunda de Imágenes (Soporta múltiples esquemas de la API de Wallapop)
                    images = []
                    raw_imgs = obj.get("images", [])
                    if isinstance(raw_imgs, list):
                        for img in raw_imgs:
                            if isinstance(img, dict):
                                # Esquema 1: { original: "...", medium: "..." }
                                url_img = img.get("original") or img.get("x-large") or img.get("medium") or img.get("small")
                                # Esquema 2: { urls: { big: "...", extra_large: "..." } }
                                if not url_img and "urls" in img and isinstance(img["urls"], dict):
                                    url_img = img["urls"].get("big") or img["urls"].get("extra_large") or img["urls"].get("medium")
                                if url_img:
                                    images.append(url_img)
                            elif isinstance(img, str) and img.startswith("http"):
                                images.append(img)

                    # Fallback directo al CDN estático si la API no envió array de imágenes
                    if not images:
                        images.append(f"https://cdn.wallapop.com/images/10420/item/{item_id}.jpg")

                    if title:
                        seen_ids.add(item_id)
                        items.append(
                            WallapopItem(
                                id=item_id,
                                titulo=title,
                                precio=price,
                                url_anuncio=item_url,
                                images_hd_urls=images
                            )
                        )

            except Exception as e:
                print(f"[!] Error durante la navegación con Playwright: {e}")
            finally:
                await browser.close()

        print(f"[+] Se encontraron {len(items)} artículos únicos válidos.")
        return items