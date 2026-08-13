from typing import List, Optional
from pydantic import BaseModel, Field


class WallapopItem(BaseModel):
    id: str
    titulo: str
    descripcion: str = ""
    precio: float
    url_anuncio: str
    images_hd_urls: List[str] = Field(default_factory=list)


class CoinVisionAnalysis(BaseModel):
    moneda_detectada: str
    peso_g: float
    ley: float
    confianza: float = 1.0


class ArbitrageResult(BaseModel):
    item: WallapopItem
    analysis: Optional[CoinVisionAnalysis] = None
    melt_value: float
    margen_chollo: float
    es_chollo: bool