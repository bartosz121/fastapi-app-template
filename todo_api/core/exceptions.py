class ApplicationError(Exception):
    """Base exception for failures that are independent of a delivery mechanism."""

    def __init__(self, detail: str | None = None, *, code: str | None = None) -> None:
        self.detail = detail
        self.code = code
        super().__init__(detail)


__all__ = ("ApplicationError",)
