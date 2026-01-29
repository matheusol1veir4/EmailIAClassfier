from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import bcrypt
from jose import jwt

from app.core.config import get_settings


settings = get_settings()


def hash_password(password: str) -> str:
    """Gera o hash seguro de uma senha utilizando bcrypt."""
    password_bytes = password.encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica se a senha informada corresponde ao hash armazenado."""
    password_bytes = password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: Dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Cria um token JWT com os dados e expiracao definidos."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> Dict[str, Any]:
    """Decodifica e valida um token JWT retornando o payload."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
