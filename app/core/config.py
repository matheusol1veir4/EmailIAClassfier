from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centraliza configuracoes da aplicacao a partir de variaveis de ambiente."""

    db_user: str = ""
    db_password: str = ""
    db_name: str = ""
    database_url: str = ""
    seed_email: str = ""
    seed_password: str = ""
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    huggingface_api_key: str = ""
    huggingface_model: str = "joeddav/xlm-roberta-base-xnli"
    huggingface_endpoint_base: str = "https://router.huggingface.co/hf-inference/models"
    llm_api_key: str = ""
    llm_endpoint: str = "https://openrouter.ai/api/v1/chat/completions"
    llm_model: str = "tngtech/deepseek-r1t2-chimera:free"
    openrouter_referer: str = ""
    openrouter_title: str = ""
    debug: bool = False
    seed_enabled: bool = False
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    """Retorna configuracoes carregadas em cache para reutilizacao."""
    return Settings()
