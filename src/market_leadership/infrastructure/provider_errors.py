class ProviderRequestError(RuntimeError):
    def __init__(
        self,
        provider_id: str,
        operation: str,
        *,
        retryable: bool,
        status_code: int | None = None,
    ) -> None:
        detail = f"Provider {provider_id} failed during {operation}"
        if status_code is not None:
            detail += f" (HTTP {status_code})"
        super().__init__(detail)
        self.provider_id = provider_id
        self.operation = operation
        self.retryable = retryable
        self.status_code = status_code


def retryable_status_code(error: Exception) -> int | None:
    status = getattr(error, "status_code", None)
    if status is None:
        status = getattr(error, "status", None)
    return status if isinstance(status, int) else None


def is_retryable_provider_failure(error: Exception) -> bool:
    status_code = retryable_status_code(error)
    return (
        status_code == 429
        or (status_code is not None and 500 <= status_code <= 599)
        or isinstance(error, (TimeoutError, ConnectionError, OSError))
    )
