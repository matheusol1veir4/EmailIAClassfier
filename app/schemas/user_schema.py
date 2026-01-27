from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    """Define o retorno de dados do usuario autenticado."""

    id: int
    email_institucional: EmailStr
    must_change_password: bool
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    """Define o payload de criacao de usuario interno."""

    email_institucional: EmailStr
    senha: str


class UserUpdate(BaseModel):
    """Define o payload de atualizacao de usuario."""

    email_institucional: Optional[EmailStr] = None
    must_change_password: Optional[bool] = None
