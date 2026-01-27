from fastapi import FastAPI


def create_app() -> FastAPI:
    """Criar e configurar a instancia principal do FastAPI."""
    app = FastAPI(title="Email AI Classifier")
    return app


app = create_app()
