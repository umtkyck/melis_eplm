"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MELIS ePLM"
    database_url: str = "sqlite+aiosqlite:///./eplm.db"
    debug: bool = False
    api_prefix: str = "/api/v1"

    model_config = {"env_prefix": "EPLM_"}


settings = Settings()
