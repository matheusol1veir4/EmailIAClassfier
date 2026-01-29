from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centraliza configuracoes da aplicacao a partir de variaveis de ambiente."""

    db_user: str = "emailClassifier"
    db_password: str = "postgres123"
    db_name: str = "emailClassifier"
    database_url: str = "postgresql://emailClassifier:postgres123@localhost:5432/emailClassifier"
    seed_email: str = ""
    seed_password: str = ""
    secret_key: str = "troque_por_uma_chave_forte"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    huggingface_api_key: str = ""
    huggingface_model: str = "joeddav/xlm-roberta-large-xnli"
    llm_api_key: str = ""
    llm_endpoint: str = "https://api.openai.com/v1/chat/completions"
    llm_model: str = "gpt-4o-mini"
    debug: bool = False
    seed_enabled: bool = True
    environment: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Retorna configuracoes carregadas em cache para reutilizacao."""
    return Settings()
