from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_NAME: str = "Wallapop Arbitrage Agent"
    TELEGRAM_BOT_TOKEN: str = ""
    GEMINI_API_KEY: str = ""
    
    # Parámetros por defecto para metales (Fase 2)
    ENABLE_VISION_STAGE: bool = False  # Switch para activar Fase 2 cuando esté lista
    DEFAULT_SILVER_MARGIN_THRESHOLD: float = 0.15  # 15% de margen mínimo de chollo

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()