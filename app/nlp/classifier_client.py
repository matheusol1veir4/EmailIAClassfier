from typing import Dict, List

import requests

from app.core.config import get_settings


class ClassifierClient:
    """Integra classificacao zero-shot via Hugging Face Inference API."""

    def __init__(self) -> None:
        """Inicializa o cliente com configuracoes do ambiente."""
        settings = get_settings()
        self._api_key = settings.huggingface_api_key
        self._model = "facebook/bart-large-mnli"
        self._endpoint = f"https://api-inference.huggingface.co/models/{self._model}"
        self._labels: List[str] = ["Produtivo", "Improdutivo"]

    def classify_email(self, text: str) -> Dict[str, float | str]:
        """Classifica um texto retornando label e score."""
        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {
            "inputs": text,
            "parameters": {"candidate_labels": self._labels},
        }
        response = requests.post(self._endpoint, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        label = data["labels"][0]
        score = float(data["scores"][0])
        return {"label": label, "score": score}
