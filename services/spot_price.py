class SpotPriceService:
    """Hook para obtener el valor del metal por gramo en tiempo real."""
    
    async def get_silver_spot_price_per_gram(self) -> float:
        # FASE 2: Conectar con YFinance (SI=F) o MetalPrice API
        # Valor estimado temporal para desarrollo: 0.85 €/g
        return 0.85