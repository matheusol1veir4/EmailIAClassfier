from fastapi import FastAPI

from app.api.v1.auth_router import router as auth_router
from app.api.v1.email_router import router as email_router
from app.api.v1.health_router import router as health_router
from app.core.database import create_db_and_tables


def create_app() -> FastAPI:
    """Cria e configura a instancia principal do FastAPI."""
    app = FastAPI(title="Email AI Classifier")
    app.include_router(auth_router)
    app.include_router(email_router)
    app.include_router(health_router)

    @app.on_event("startup")
    def on_startup() -> None:
        """Inicializa recursos essenciais da aplicacao."""
        create_db_and_tables()

    return app


app = create_app()
