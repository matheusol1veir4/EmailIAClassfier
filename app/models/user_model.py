from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Representa um usuario persistido na base de dados."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email_institucional: str = Field(index=True, unique=True, nullable=False, max_length=255)
    password_hash: str = Field(nullable=False, max_length=255)
    must_change_password: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
