import logging
from typing import Dict, List

import requests

from app.core.config import get_settings
from app.nlp.exceptions import ConfigurationError, ExternalServiceError


class ClassifierClient:
    """Integra classificacao zero-shot via Hugging Face Inference API."""

    def __init__(self) -> None:
        """Inicializa o cliente com configuracoes do ambiente."""
        settings = get_settings()
        self._api_key = settings.huggingface_api_key
        self._model = settings.huggingface_model
        base = settings.huggingface_endpoint_base.rstrip("/")
        self._endpoint = f"{base}/{self._model}"
        self._labels: List[str] = [
            "Produtivo (trabalho, suporte, financeiro, operacoes)",
            "Improdutivo (pessoal, irrelevante, sem acao)",
            "Propaganda (marketing, oferta, promocao, spam)",
        ]
        self._label_aliases = {
            "Produtivo": "Produtivo",
            "Improdutivo": "Improdutivo",
            "Propaganda": "Propaganda",
        }
        self._hypothesis_template = "Este email trata principalmente de {}."
        self._logger = logging.getLogger(__name__)

    def classify_email(self, text: str) -> Dict[str, float | str]:
        """Classifica um texto retornando label e score."""
        if not self._api_key:
            raise ConfigurationError("HUGGINGFACE_API_KEY nao configurada")
        normalized_text = self._strip_signature(text)
        guideline = (
            "Regra: se o email contiver palavras como urgente,prioridade, urgentissimo ou solicito,preciso, envie uma equipe, tiver algum prazo para resposta, aguardo retorno"
            "considere como Produtivo.\n\n"
        )
        normalized_text = f"{guideline}{normalized_text}"
        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {
            "inputs": normalized_text,
            "parameters": {
                "candidate_labels": self._labels,
                "hypothesis_template": self._hypothesis_template,
            },
        }
        try:
            response = requests.post(self._endpoint, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response else None
            detail = exc.response.text if exc.response else str(exc)
            raise ExternalServiceError(
                service="Hugging Face Inference API",
                detail=f"Resposta {status_code}: {detail}",
                status_code=status_code,
                endpoint=self._endpoint,
            ) from exc
        except requests.RequestException as exc:
            raise ExternalServiceError(
                service="Hugging Face Inference API",
                detail=f"Falha de rede: {exc}",
                endpoint=self._endpoint,
            ) from exc
        data = response.json()
        if isinstance(data, dict) and data.get("error"):
            raise ExternalServiceError(
                service="Hugging Face Inference API",
                detail=str(data["error"]),
                status_code=response.status_code,
                endpoint=self._endpoint,
            )
        label = data["labels"][0]
        normalized = self._normalize_label(label)
        score = float(data["scores"][0])
        self._log_scores(data)
        return {"label": normalized, "score": score}

    def _normalize_label(self, label: str) -> str:
        """Normaliza o rotulo retornado pela API para um nome canonico."""
        if not isinstance(label, str):
            return str(label)
        prefix = label.split("(", 1)[0].strip()
        return self._label_aliases.get(prefix, prefix)

    def _strip_signature(self, text: str) -> str:
        """Remove assinaturas/rodapes comuns para reduzir ruido."""
        if not isinstance(text, str):
            return str(text)
        markers = [
            "\nAtenciosamente",
            "\nAtt",
            "\nAbraços",
            "\nObrigado",
            "\nObrigada",
            "\nCordialmente",
        ]
        lowered = text.lower()
        for marker in markers:
            idx = lowered.find(marker.lower())
            if idx != -1:
                return text[:idx].strip()
        return text.strip()

    def _log_scores(self, data: Dict[str, object]) -> None:
        """Loga scores e labels retornados pelo modelo para diagnostico."""
        if not isinstance(data, dict):
            return
        labels = data.get("labels")
        scores = data.get("scores")
        if isinstance(labels, list) and isinstance(scores, list):
            pairs = list(zip(labels, scores))
            self._logger.info("HuggingFace scores: %s", pairs)
