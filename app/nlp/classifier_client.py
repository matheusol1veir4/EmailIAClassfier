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
        self._labels: List[str] = ["Produtivo", "Improdutivo"]

    def classify_email(self, text: str) -> Dict[str, float | str]:
        """Classifica um texto retornando label e score."""
        if not self._api_key:
            raise ConfigurationError("HUGGINGFACE_API_KEY nao configurada")
        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {
            "inputs": text,
            "parameters": {"candidate_labels": self._labels},
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
        score = float(data["scores"][0])
        return {"label": label, "score": score}
