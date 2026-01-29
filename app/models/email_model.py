from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class Email(SQLModel, table=True):
    """Representa um email processado e armazenado na base de dados."""

    __tablename__ = "emails"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    email_destinatario: str = Field(nullable=False, max_length=255)
    assunto: Optional[str] = Field(default=None, max_length=255)
    raw_body: str = Field(nullable=False)
    classification: str = Field(nullable=False, max_length=50)
    generated_response: Optional[str] = Field(default=None, nullable=True)
    respondido: bool = Field(default=False)
    respondido_em: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
