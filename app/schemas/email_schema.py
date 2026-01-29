from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class EmailClassifyRequest(BaseModel):
    """Define o payload para classificacao de email."""

    email_body: str
    email_destinatario: EmailStr
    assunto: Optional[str] = None


class EmailResponse(BaseModel):
    """Define o retorno da classificacao de email."""

    id: int
    classification: str
    generated_response: Optional[str]
    email_destinatario: EmailStr


class EmailHistoryItem(BaseModel):
    """Define o item retornado no historico de emails."""

    id: int
    email_destinatario: EmailStr
    assunto: Optional[str]
    classification: str
    respondido: bool
    respondido_em: Optional[datetime]
    created_at: datetime


class EmailHistoryResponse(BaseModel):
    """Define o retorno do historico de emails com total."""

    emails: list[EmailHistoryItem]
    total: int


class EmailDetailResponse(BaseModel):
    """Define o retorno detalhado de um email."""

    id: int
    email_body: str
    email_destinatario: EmailStr
    assunto: Optional[str]
    classification: str
    generated_response: Optional[str]
    respondido: bool
    respondido_em: Optional[datetime]
    created_at: datetime
