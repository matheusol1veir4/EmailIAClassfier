from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import decode_token
from app.models.user_model import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import ChangePasswordRequest, LoginRequest, MessageResponse, TokenResponse
from app.schemas.user_schema import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_user_repository(session: Annotated[Session, Depends(get_session)]) -> UserRepository:
    """Fornece repositorio de usuarios para uso nas rotas."""
    return UserRepository(session)


def get_auth_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    """Fornece o servico de autenticacao para uso nas rotas."""
    return AuthService(user_repository)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    """Recupera o usuario autenticado a partir do token JWT."""
    try:
        payload = decode_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido")
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido") from exc

    user = user_repository.get_by_email(email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario nao encontrado")
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Autentica usuario e retorna token JWT."""
    try:
        return auth_service.login(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """Permite trocar a senha do usuario autenticado."""
    try:
        auth_service.change_password(current_user, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MessageResponse(mensagem="Senha alterada com sucesso")


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Retorna os dados do usuario autenticado."""
    return auth_service.get_me(current_user)
