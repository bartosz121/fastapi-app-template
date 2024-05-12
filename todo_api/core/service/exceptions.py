from todo_api.core.exceptions import BaseError


class ServiceError(BaseError): ...


class ConflictError(ServiceError): ...


class NotFoundError(ServiceError): ...
