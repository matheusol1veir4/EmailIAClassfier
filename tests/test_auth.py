import httpx
from sqlmodel import Session

from app.core.security import hash_password
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


def test_login_and_me(client: httpx.Client, db_session: Session) -> None:
    """Valida o login e o endpoint /me."""
    _ = create_user(db_session, "usuario@empresa.com", "senha123")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "usuario@empresa.com", "senha": "senha123"},
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["email_institucional"] == "usuario@empresa.com"


def test_login_invalid_password(client: httpx.Client, db_session: Session) -> None:
    """Garante que senha invalida retorna 401."""
    _ = create_user(db_session, "usuario@empresa.com", "senha123")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "usuario@empresa.com", "senha": "errada123"},
    )

    assert response.status_code == 401
