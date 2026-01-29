class ConfigurationError(RuntimeError):
    """Erro de configuracao da aplicacao (ex.: chaves nao definidas)."""


class ExternalServiceError(RuntimeError):
    """Erro ao chamar servicos externos de IA."""

    def __init__(
        self,
        service: str,
        detail: str,
        status_code: int | None = None,
        endpoint: str | None = None,
    ) -> None:
        self.service = service
        self.detail = detail
        self.status_code = status_code
        self.endpoint = endpoint
        super().__init__(detail)

