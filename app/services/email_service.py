from datetime import datetime, timezone
from typing import Any, List

from app.models.email_model import Email
from app.repositories.email_repository import EmailRepository
from app.schemas.email_schema import (
    EmailDetailResponse,
    EmailHistoryItem,
    EmailHistoryResponse,
    EmailResponse,
)


class EmailService:
    """Orquestra o fluxo de processamento, classificacao e persistencia de emails."""

    def __init__(self, email_repository: EmailRepository, classifier_client: Any, llm_client: Any) -> None:
        """Inicializa o servico com repositorio e clientes de NLP/LLM."""
        self._email_repository = email_repository
        self._classifier_client = classifier_client
        self._llm_client = llm_client

    def process_email(
        self,
        user_id: int,
        email_body: str,
        email_destinatario: str,
        assunto: str | None = None,
    ) -> EmailResponse:
        """Processa um email e retorna apenas a classificacao."""
        classification_input = email_body
        if assunto:
            classification_input = f"Assunto: {assunto}\n\n{email_body}"
        classification_result = self._classifier_client.classify_email(classification_input)
        classification = self._extract_label(classification_result)

        email = Email(
            user_id=user_id,
            email_destinatario=email_destinatario,
            assunto=assunto,
            raw_body=email_body,
            classification=classification,
            generated_response=None,
        )
        saved_email = self._email_repository.create(email)

        return EmailResponse(
            id=saved_email.id or 0,
            classification=saved_email.classification,
            generated_response=saved_email.generated_response,
            email_destinatario=saved_email.email_destinatario,
        )

    def generate_response(self, email_id: int, user_id: int) -> EmailDetailResponse:
        """Gera resposta sugerida para um email ja classificado."""
        email = self._email_repository.get_by_id_for_user(email_id, user_id)
        if email is None:
            raise ValueError("Email nao encontrado")
        if not email.classification:
            raise ValueError("Email sem classificacao")

        generated = self._llm_client.generate_response(email.classification, email.raw_body).strip()
        if not generated:
            raise ValueError("Resposta vazia gerada pelo modelo")
        email.generated_response = generated
        email.updated_at = datetime.utcnow()
        updated = self._email_repository.update(email)
        return self._to_detail_response(updated)

    def mark_responded(self, email_id: int, user_id: int) -> EmailDetailResponse:
        """Marca um email do usuario como respondido e retorna os dados atualizados."""
        email = self._email_repository.get_by_id_for_user(email_id, user_id)
        if email is None:
            raise ValueError("Email nao encontrado")

        email.respondido = True
        email.respondido_em = datetime.now(timezone.utc)
        email.updated_at = datetime.now(timezone.utc)
        updated = self._email_repository.update(email)
        return self._to_detail_response(updated)

    def list_history(self, user_id: int, respondido: bool | None = None) -> EmailHistoryResponse:
        """Lista emails do usuario com filtro opcional por status de resposta."""
        emails = self._email_repository.list_by_user(user_id, respondido)
        total = self._email_repository.count_by_user(user_id, respondido)
        return EmailHistoryResponse(
            emails=[self._to_history_item(email) for email in emails],
            total=total,
        )

    def get_email_detail(self, email_id: int, user_id: int) -> EmailDetailResponse:
        """Retorna o detalhe de um email especifico do usuario."""
        email = self._email_repository.get_by_id_for_user(email_id, user_id)
        if email is None:
            raise ValueError("Email nao encontrado")
        return self._to_detail_response(email)

    def _extract_label(self, classification_result: Any) -> str:
        """Extrai o rotulo de classificacao retornado pelo cliente NLP."""
        if isinstance(classification_result, dict):
            label = classification_result.get("label")
            if label:
                return str(label)
        return str(classification_result)

    def _to_history_item(self, email: Email) -> EmailHistoryItem:
        """Converte uma entidade Email em item de historico."""
        return EmailHistoryItem(
            id=email.id or 0,
            email_destinatario=email.email_destinatario,
            assunto=email.assunto,
            classification=email.classification,
            respondido=email.respondido,
            respondido_em=email.respondido_em,
            created_at=email.created_at,
        )

    def _to_detail_response(self, email: Email) -> EmailDetailResponse:
        """Converte uma entidade Email em resposta detalhada."""
        return EmailDetailResponse(
            id=email.id or 0,
            email_body=email.raw_body,
            email_destinatario=email.email_destinatario,
            assunto=email.assunto,
            classification=email.classification,
            generated_response=email.generated_response,
            respondido=email.respondido,
            respondido_em=email.respondido_em,
            created_at=email.created_at,
        )
