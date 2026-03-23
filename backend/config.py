from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LLM
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model: str = "openai/gpt-4o-mini"

    # Database
    database_url: str = "sqlite+aiosqlite:///./platformgen.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Confidence thresholds
    high_confidence_threshold: float = 0.85
    medium_confidence_threshold: float = 0.60
    low_confidence_threshold: float = 0.40

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
