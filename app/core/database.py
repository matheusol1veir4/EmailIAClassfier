from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings


settings = get_settings()
engine = create_engine(settings.database_url, echo=settings.debug)


def get_session() -> Generator[Session, None, None]:
    """Fornece uma sessao de banco para uso em dependencias."""
    with Session(engine) as session:
        yield session


def create_db_and_tables() -> None:
    """Cria as tabelas no banco com base nos modelos registrados."""
    SQLModel.metadata.create_all(engine)
