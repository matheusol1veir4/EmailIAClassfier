from io import BytesIO
from typing import Annotated, Optional

import pdfplumber
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session

from app.api.v1.auth_router import get_current_user
from app.core.database import get_session
from app.models.user_model import User
from app.nlp.classifier_client import ClassifierClient
from app.nlp.llm_client import LlmClient
from app.repositories.email_repository import EmailRepository
from app.schemas.email_schema import EmailDetailResponse, EmailHistoryItem, EmailResponse
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/v1/emails", tags=["emails"])


def get_email_repository(session: Annotated[Session, Depends(get_session)]) -> EmailRepository:
    """Fornece repositorio de emails para uso nas rotas."""
    return EmailRepository(session)


def get_email_service(
    email_repository: Annotated[EmailRepository, Depends(get_email_repository)],
) -> EmailService:
    """Fornece o servico de emails para uso nas rotas."""
    return EmailService(email_repository, ClassifierClient(), LlmClient())


def extract_text_from_file(file: UploadFile) -> str:
    """Extrai texto de arquivos TXT ou PDF enviados na requisicao."""
    filename = (file.filename or "").lower()
    content = file.file.read()
    if filename.endswith(".pdf"):
        with pdfplumber.open(BytesIO(content)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages)
    return content.decode("utf-8", errors="ignore")


@router.post("/classify", response_model=EmailResponse)
def classify_email(
    current_user: Annotated[User, Depends(get_current_user)],
    email_body: Annotated[Optional[str], Form(default=None)],
    email_destinatario: Annotated[str, Form(...)],
    assunto: Annotated[Optional[str], Form(default=None)],
    arquivo: Annotated[Optional[UploadFile], File(default=None)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> EmailResponse:
    """Processa o email recebido e retorna classificacao e resposta sugerida."""
    if email_body is None and arquivo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email vazio")

    if arquivo is not None:
        email_body = extract_text_from_file(arquivo)

    if not email_body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email vazio")

    return email_service.process_email(current_user.id or 0, email_body, email_destinatario, assunto)


@router.post("/{email_id}/mark-responded", response_model=EmailDetailResponse)
def mark_responded(
    email_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> EmailDetailResponse:
    """Marca um email como respondido."""
    _ = current_user
    try:
        return email_service.mark_responded(email_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/history", response_model=list[EmailHistoryItem])
def get_history(
    current_user: Annotated[User, Depends(get_current_user)],
    respondido: Optional[bool] = None,
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> list[EmailHistoryItem]:
    """Retorna o historico de emails do usuario autenticado."""
    return email_service.list_history(current_user.id or 0, respondido)


@router.get("/{email_id}", response_model=EmailDetailResponse)
def get_email_detail(
    email_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> EmailDetailResponse:
    """Retorna o detalhe de um email especifico."""
    _ = current_user
    try:
        return email_service.get_email_detail(email_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
