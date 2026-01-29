import httpx
import pytest
from sqlmodel import Session

from app.core.security import hash_password
from app.models.email_model import Email
from app.models.user_model import User


def create_user(session: Session, email: str, senha: str) -> User:
    """Cria um usuario para uso nos testes."""
    user = User(
        email_institucional=email,
        password_hash=hash_password(senha),
        must_change_password=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_email(session: Session, user_id: int) -> Email:
    """Cria um email associado ao usuario informado."""
    email = Email(
        user_id=user_id,
        email_destinatario="cliente@empresa.com",
        assunto="Teste",
        raw_body="Conteudo do email",
        classification="Produtivo",
        generated_response="Resposta sugerida",
    )
    session.add(email)
    session.commit()
    session.refresh(email)
    return email


async def login_and_get_token(client: httpx.AsyncClient, email: str, senha: str) -> str:
    """Autentica usuario e retorna token."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "senha": senha},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_email_ownership_enforced(client: httpx.AsyncClient, db_session: Session) -> None:
    """Garante que usuario nao acessa emails de outro usuario."""
    user_a = create_user(db_session, "usera@empresa.com", "senha123")
    _ = create_user(db_session, "userb@empresa.com", "senha123")
    email = create_email(db_session, user_a.id or 0)

    token = await login_and_get_token(client, "userb@empresa.com", "senha123")
    headers = {"Authorization": f"Bearer {token}"}

    detail_response = await client.get(f"/api/v1/emails/{email.id}", headers=headers)
    assert detail_response.status_code == 404

    mark_response = await client.post(f"/api/v1/emails/{email.id}/mark-responded", headers=headers)
    assert mark_response.status_code == 404


@pytest.mark.asyncio
async def test_classify_email_with_mocked_ai(app, client: httpx.AsyncClient, db_session: Session) -> None:
    """Valida o fluxo de classificacao com IA mockada."""
    user = create_user(db_session, "mock@empresa.com", "senha123")
    token = await login_and_get_token(client, "mock@empresa.com", "senha123")
    headers = {"Authorization": f"Bearer {token}"}

    from app.api.v1.email_router import get_email_service
    from app.repositories.email_repository import EmailRepository
    from app.services.email_service import EmailService

    class FakeClassifierClient:
        """Cliente fake para classificacao."""

        def classify_email(self, text: str):
            """Retorna classificacao deterministica."""
            _ = text
            return {"label": "Produtivo", "score": 0.99}

    class FakeLlmClient:
        """Cliente fake para geracao de resposta."""

        def generate_response(self, classification: str, email_body: str) -> str:
            """Retorna resposta fixa para testes."""
            return f"Resposta simulada para {classification}: {email_body[:20]}"

    def override_email_service():
        """Substitui o servico de email com clientes fake."""
        repository = EmailRepository(db_session)
        return EmailService(repository, FakeClassifierClient(), FakeLlmClient())

    app.dependency_overrides[get_email_service] = override_email_service
    try:
        response = await client.post(
            "/api/v1/emails/classify",
            headers=headers,
            data={
                "email_destinatario": "cliente@empresa.com",
                "assunto": "Teste",
                "email_body": "Conteudo de teste para IA",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "Produtivo"
    assert payload["generated_response"].startswith("Resposta simulada")
    assert payload["email_destinatario"] == "cliente@empresa.com"

    saved = db_session.get(Email, payload["id"])
    assert saved is not None
    assert saved.user_id == user.id
