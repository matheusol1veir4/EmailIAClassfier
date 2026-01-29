from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.auth_router import router as auth_router
from app.api.v1.email_router import router as email_router
from app.api.v1.health_router import router as health_router
from app.core.config import get_settings
from app.core.database import create_db_and_tables
from app.core.seed_user import seed_user
from app.web.web_router import router as web_router


def create_app() -> FastAPI:
    """Cria e configura a instancia principal do FastAPI."""
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Inicializa recursos essenciais da aplicacao."""
        if settings.environment == "development":
            create_db_and_tables()
            if settings.seed_enabled:
                seed_user()
        yield

    app = FastAPI(title="Email AI Classifier", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
    app.include_router(web_router)
    app.include_router(auth_router)
    app.include_router(email_router)
    app.include_router(health_router)

    return app


app = create_app()
