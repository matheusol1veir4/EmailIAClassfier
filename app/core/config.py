from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centraliza configuracoes da aplicacao a partir de variaveis de ambiente."""

    db_user: str = "emailClassifier"
    db_password: str = "postgres123"
    db_name: str = "emailClassifier"
    database_url: str = "postgresql://emailClassifier:postgres123@localhost:5432/emailClassifier"
    secret_key: str = "troque_por_uma_chave_forte"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    huggingface_api_key: str = ""
    llm_api_key: str = ""
    debug: bool = False
    environment: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Retorna configuracoes carregadas em cache para reutilizacao."""
    return Settings()
