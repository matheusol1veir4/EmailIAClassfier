from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user_model import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import ChangePasswordRequest, LoginRequest, TokenResponse
from app.schemas.user_schema import UserResponse


class AuthService:
    """Centraliza regras de negocio relacionadas a autenticacao de usuarios."""

    def __init__(self, user_repository: UserRepository) -> None:
        """Inicializa o servico com o repositorio de usuarios."""
        self._user_repository = user_repository
        self._settings = get_settings()

    def login(self, payload: LoginRequest) -> TokenResponse:
        """Autentica o usuario e gera token de acesso JWT."""
        user = self._user_repository.get_by_email(payload.email)
        if user is None or not verify_password(payload.senha, user.password_hash):
            raise ValueError("Credenciais invalidas")

        access_token = create_access_token(
            data={"sub": user.email_institucional, "user_id": user.id},
            expires_delta=timedelta(minutes=self._settings.access_token_expire_minutes),
        )
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            must_change_password=user.must_change_password,
        )

    def change_password(self, user: User, payload: ChangePasswordRequest) -> None:
        """Atualiza a senha do usuario autenticado."""
        if not verify_password(payload.senha_atual, user.password_hash):
            raise ValueError("Senha atual invalida")

        user.password_hash = hash_password(payload.nova_senha)
        user.must_change_password = False
        user.updated_at = datetime.now(timezone.utc)
        self._user_repository.update(user)

    def get_me(self, user: User) -> UserResponse:
        """Retorna os dados do usuario autenticado."""
        return UserResponse(
            id=user.id or 0,
            email_institucional=user.email_institucional,
            must_change_password=user.must_change_password,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
