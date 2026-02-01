import logging
from typing import Dict

import requests

from app.core.config import get_settings
from app.nlp.exceptions import ConfigurationError, ExternalServiceError

logger = logging.getLogger(__name__)


class LlmClient:
    """Integra geracao de resposta via provedor LLM configurado."""

    def __init__(self) -> None:
        """Inicializa o cliente com configuracoes do ambiente."""
        settings = get_settings()
        self._api_key = settings.llm_api_key
        self._endpoint = settings.llm_endpoint
        self._model = settings.llm_model
        self._openrouter_referer = settings.openrouter_referer
        self._openrouter_title = settings.openrouter_title

    def generate_response(self, classification: str, email_body: str) -> str:
        """Gera uma resposta automatica baseada na classificacao e no email."""
        if not self._api_key:
            raise ConfigurationError("LLM_API_KEY nao configurada")
        prompt = self._build_prompt(classification, email_body)
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": "Voce e um assistente que escreve respostas profissionais de email."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
            "max_tokens": 128,
        }
        headers = self._build_headers()
        try:
            response = requests.post(self._endpoint, headers=headers, json=payload, timeout=300)
            response.raise_for_status()
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response else None
            detail = exc.response.text if exc.response else str(exc)
            if exc.response is not None and status_code == 429:
                rate_limit_context = self._extract_rate_limit_context(exc.response.headers)
                logger.warning(
                    "Falha no provedor de IA: service=LLM status=%s endpoint=%s %s",
                    status_code,
                    self._endpoint,
                    rate_limit_context,
                )
                detail = f"Limite de uso atingido. {rate_limit_context}".strip()
            raise ExternalServiceError(
                service="LLM",
                detail=f"Resposta {status_code}: {detail}",
                status_code=status_code,
                endpoint=self._endpoint,
            ) from exc
        except requests.RequestException as exc:
            raise ExternalServiceError(
                service="LLM",
                detail=f"Falha de rede: {exc}",
                endpoint=self._endpoint,
            ) from exc
        data = response.json()
        if isinstance(data, dict) and data.get("error"):
            raise ExternalServiceError(
                service="LLM",
                detail=str(data["error"]),
                status_code=response.status_code,
                endpoint=self._endpoint,
            )
        return data["choices"][0]["message"]["content"].strip()

    def _build_prompt(self, classification: str, email_body: str) -> str:
        """Construi o prompt para gerar resposta adequada ao contexto do email."""
        return (
            "Voce e um assistente de suporte que redige respostas profissionais por email.\n"
            "Responda em portugues brasileiro, com tom educado e objetivo.\n"
            "Se a mensagem for propaganda, decline de forma cordial e encerre.\n"
            "Se for improdutivo, responda de forma breve e nao incentive a conversa.\n"
            "Se for produtivo, proponha o proximo passo claro.\n\n"
            "Classificacao: "
            f"{classification}.\n"
            "Email:\n"
            f"{email_body}\n\n"
            "Regras: responda em 3 a 6 frases, sem markdown, sem listas, sem assinaturas longas."
        )

    def _build_headers(self) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        if self._openrouter_referer:
            headers["HTTP-Referer"] = self._openrouter_referer
        if self._openrouter_title:
            headers["X-Title"] = self._openrouter_title
        return headers

    def _extract_rate_limit_context(self, headers: Dict[str, str]) -> str:
        """Extrai informacoes de rate limit e request id dos headers."""
        keys = [
            "x-request-id",
            "x-ratelimit-limit-requests",
            "x-ratelimit-remaining-requests",
            "x-ratelimit-reset-requests",
            "x-ratelimit-limit-tokens",
            "x-ratelimit-remaining-tokens",
            "x-ratelimit-reset-tokens",
            "retry-after",
        ]
        parts = []
        for key in keys:
            value = headers.get(key)
            if value:
                parts.append(f"{key}={value}")
        return " ".join(parts)
