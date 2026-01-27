from typing import Dict

import requests

from app.core.config import get_settings


class LlmClient:
    """Integra geracao de resposta via provedor LLM configurado."""

    def __init__(self) -> None:
        """Inicializa o cliente com configuracoes do ambiente."""
        settings = get_settings()
        self._api_key = settings.llm_api_key
        self._endpoint = "https://api.openrouter.ai/v1/chat/completions"
        self._model = "meta-llama/llama-3.1-8b-instruct"

    def generate_response(self, classification: str, email_body: str) -> str:
        """Gera uma resposta automatica baseada na classificacao e no email."""
        prompt = self._build_prompt(classification, email_body)
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": "Voce e um assistente que escreve respostas profissionais de email."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(self._endpoint, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    def _build_prompt(self, classification: str, email_body: str) -> str:
        """Construi o prompt para gerar resposta adequada ao contexto do email."""
        return (
            "Classificacao: "
            f"{classification}.\n"
            "Email:\n"
            f"{email_body}\n\n"
            "Escreva uma resposta curta, educada e objetiva em portugues brasileiro."
        )
