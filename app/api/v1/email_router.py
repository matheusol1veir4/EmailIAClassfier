from io import BytesIO
import logging
from typing import Annotated, Optional

import pdfplumber
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session

from app.api.v1.auth_router import get_current_user
from app.core.database import get_session
from app.models.user_model import User
from app.nlp.classifier_client import ClassifierClient
from app.nlp.exceptions import ConfigurationError, ExternalServiceError
from app.nlp.llm_client import LlmClient
from app.repositories.email_repository import EmailRepository
from app.schemas.email_schema import EmailDetailResponse, EmailHistoryResponse, EmailResponse
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/v1/emails", tags=["emails"])
logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
ALLOWED_EXTENSIONS = {".txt", ".pdf"}
ALLOWED_MIME_TYPES = {"text/plain", "application/pdf"}


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
    if not any(filename.endswith(extension) for extension in ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de arquivo nao suportado")
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de arquivo nao suportado")
    content = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo excede o limite permitido")
    if filename.endswith(".pdf"):
        with pdfplumber.open(BytesIO(content)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages)
    return content.decode("utf-8", errors="ignore")


@router.post("/classify", response_model=EmailResponse)
def classify_email(
    current_user: Annotated[User, Depends(get_current_user)],
    email_destinatario: Annotated[str, Form(...)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
    email_body: Annotated[Optional[str], Form()] = None,
    assunto: Annotated[Optional[str], Form()] = None,
    arquivo: Annotated[Optional[UploadFile], File()] = None,
) -> EmailResponse:
    """Processa o email recebido e retorna classificacao e resposta sugerida."""
    if email_body is None and arquivo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email vazio")

    if arquivo is not None:
        email_body = extract_text_from_file(arquivo)

    if not email_body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email vazio")

    try:
        return email_service.process_email(current_user.id or 0, email_body, email_destinatario, assunto)
    except ConfigurationError as exc:
        logger.warning("Configuracao de IA invalida ou ausente: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "erro": "configuracao_ia",
                "mensagem": f"Configuracao de IA ausente ou invalida: {exc}",
                "acao": "Verifique as chaves e variaveis no .env",
            },
        ) from exc
    except ExternalServiceError as exc:
        status_label = f"Status: {exc.status_code}. " if exc.status_code else ""
        endpoint_label = f"Endpoint: {exc.endpoint}. " if exc.endpoint else ""
        logger.error(
            "Falha no provedor de IA: service=%s status=%s endpoint=%s detail=%s",
            exc.service,
            exc.status_code,
            exc.endpoint,
            exc.detail,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "erro": "falha_provedor_ia",
                "provedor": exc.service,
                "status_http": exc.status_code,
                "endpoint": exc.endpoint,
                "mensagem": f"{status_label}{endpoint_label}Detalhe: {exc.detail}".strip(),
            },
        ) from exc
    except ValueError as exc:
        logger.error("Falha ao processar email com IA: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "erro": "falha_processamento_ia",
                "mensagem": f"Falha ao processar o email com a IA: {exc}",
            },
        ) from exc


@router.post("/{email_id}/mark-responded", response_model=EmailDetailResponse)
def mark_responded(
    email_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> EmailDetailResponse:
    """Marca um email como respondido."""
    try:
        return email_service.mark_responded(email_id, current_user.id or 0)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{email_id}/generate-response", response_model=EmailDetailResponse)
def generate_response(
    email_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> EmailDetailResponse:
    """Gera a resposta sugerida para um email ja classificado."""
    try:
        return email_service.generate_response(email_id, current_user.id or 0)
    except ConfigurationError as exc:
        logger.warning("Configuracao de IA invalida ou ausente: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "erro": "configuracao_ia",
                "mensagem": f"Configuracao de IA ausente ou invalida: {exc}",
                "acao": "Verifique as chaves e variaveis no .env",
            },
        ) from exc
    except ExternalServiceError as exc:
        status_label = f"Status: {exc.status_code}. " if exc.status_code else ""
        endpoint_label = f"Endpoint: {exc.endpoint}. " if exc.endpoint else ""
        logger.error(
            "Falha no provedor de IA: service=%s status=%s endpoint=%s detail=%s",
            exc.service,
            exc.status_code,
            exc.endpoint,
            exc.detail,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "erro": "falha_provedor_ia",
                "provedor": exc.service,
                "status_http": exc.status_code,
                "endpoint": exc.endpoint,
                "mensagem": f"{status_label}{endpoint_label}Detalhe: {exc.detail}".strip(),
            },
        ) from exc
    except ValueError as exc:
        message = str(exc)
        if "resposta vazia" in message.lower():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "erro": "resposta_vazia",
                    "mensagem": "O modelo nao gerou resposta. Tente novamente.",
                },
            ) from exc
        status_code = status.HTTP_404_NOT_FOUND if "nao encontrado" in message.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message) from exc




@router.get("/history", response_model=EmailHistoryResponse)
def get_history(
    current_user: Annotated[User, Depends(get_current_user)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
    respondido: Optional[bool] = None,
) -> EmailHistoryResponse:
    """Retorna o historico de emails do usuario autenticado."""
    return email_service.list_history(current_user.id or 0, respondido)


@router.get("/{email_id}", response_model=EmailDetailResponse)
def get_email_detail(
    email_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> EmailDetailResponse:
    """Retorna o detalhe de um email especifico."""
    try:
        return email_service.get_email_detail(email_id, current_user.id or 0)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
