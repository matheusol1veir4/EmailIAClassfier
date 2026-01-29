import httpx
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


def login_and_get_token(client: httpx.Client, email: str, senha: str) -> str:
    """Autentica usuario e retorna token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "senha": senha},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_email_ownership_enforced(client: httpx.Client, db_session: Session) -> None:
    """Garante que usuario nao acessa emails de outro usuario."""
    user_a = create_user(db_session, "usera@empresa.com", "senha123")
    _ = create_user(db_session, "userb@empresa.com", "senha123")
    email = create_email(db_session, user_a.id or 0)

    token = login_and_get_token(client, "userb@empresa.com", "senha123")
    headers = {"Authorization": f"Bearer {token}"}

    detail_response = client.get(f"/api/v1/emails/{email.id}", headers=headers)
    assert detail_response.status_code == 404

    mark_response = client.post(f"/api/v1/emails/{email.id}/mark-responded", headers=headers)
    assert mark_response.status_code == 404
