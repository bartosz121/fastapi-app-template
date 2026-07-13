from todo_api.core.exceptions import ApplicationError


class DatabaseError(ApplicationError):
    """Base exception raised by the database adapter."""


class RecordNotFoundError(DatabaseError): ...


class IntegrityConstraintError(DatabaseError): ...


class DatabaseOperationError(DatabaseError): ...


__all__ = (
    "DatabaseError",
    "RecordNotFoundError",
    "IntegrityConstraintError",
    "DatabaseOperationError",
)
