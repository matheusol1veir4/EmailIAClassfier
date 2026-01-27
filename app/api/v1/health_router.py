from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("")
def health_check() -> dict:
    """Retorna status basico de disponibilidade da API."""
    return {"status": "ok"}
