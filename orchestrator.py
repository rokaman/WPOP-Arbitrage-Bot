from models import ArbitrageResult
from services.scraper import WallapopScraper
from services.vision import VisionArbitrageService


class AgentOrchestrator:
    def __init__(self, spot_service=None, vision_service=None):
        self.spot_service = spot_service
        self.scraper = WallapopScraper()
        self.vision_service = vision_service or VisionArbitrageService(self.spot_service)

    async def run_search_pipeline(self, query: str, max_price: float = 30.0):
        items = await self.scraper.search_items(query)

        results = []
        print("[*] Ejecutando Hook de Fase 2 (Visión & Arbitraje)...")
        for item in items:
            # Si el precio extraído es válido y supera el max_price, lo filtramos.
            if max_price and item.precio > 0 and item.precio > max_price:
                continue

            analysis = await self.vision_service.process_item_images(item)

            melt_value = 0.0
            margen_chollo = 0.0
            es_chollo = False

            if analysis and analysis.peso_g > 0:
                precio_gramo_plata = 0.85
                melt_value = analysis.peso_g * analysis.ley * precio_gramo_plata
                
                if item.precio > 0:
                    margen_chollo = ((melt_value - item.precio) / item.precio) * 100
                    es_chollo = margen_chollo > 15.0

            results.append(
                ArbitrageResult(
                    item=item,
                    analysis=analysis,
                    melt_value=melt_value,
                    margen_chollo=margen_chollo,
                    es_chollo=es_chollo,
                )
            )

        return results