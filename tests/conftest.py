import importlib
import os
from typing import Generator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture()
def app(tmp_path) -> FastAPI:
    """Cria uma instancia da aplicacao com banco isolado para testes."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"
    os.environ["DATABASE_URL"] = db_url
    os.environ["SECRET_KEY"] = "test-secret"
    os.environ["ALGORITHM"] = "HS256"
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "5"
    os.environ["SEED_ENABLED"] = "false"

    import app.core.config as config_module

    config_module.get_settings.cache_clear()
    importlib.reload(config_module)

    import app.core.database as database_module

    importlib.reload(database_module)
    test_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    database_module.engine = test_engine
    SQLModel.metadata.create_all(test_engine)

    import app.main as main_module

    importlib.reload(main_module)
    return main_module.create_app()


@pytest_asyncio.fixture()
async def client(app: FastAPI) -> Generator[httpx.AsyncClient, None, None]:
    """Fornece um cliente HTTP assincrono para testes de API."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Fornece sessao do banco para inserir dados de teste."""
    import app.core.database as database_module

    with Session(database_module.engine) as session:
        yield session

