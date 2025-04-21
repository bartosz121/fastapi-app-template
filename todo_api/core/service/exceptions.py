from todo_api.core.exceptions import TodoApiError


class ServiceError(TodoApiError): ...


class ConflictError(ServiceError): ...


class NotFoundError(ServiceError): ...
