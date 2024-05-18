from contextvars import ContextVar
from typing import Callable

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_SCOPE_NAME = "request_id"

request_id_ctx: ContextVar[str | None] = ContextVar("request_id_ctx", default=None)


class RequestIdMiddleware:
    app: ASGIApp
    header_name: str
    id_factory: Callable[[Scope], str]

    def __init__(
        self, app: ASGIApp, header_name: str, id_factory: Callable[[Scope], str]
    ) -> None:
        self.app = app
        self.header_name = header_name
        self.id_factory = id_factory

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request_id_ctx.set(self.id_factory(scope))

        async def send_with_request_id_header(message: Message) -> None:
            request_id = request_id_ctx.get()

            if message["type"] == "http.response.start" and request_id:
                headers = MutableHeaders(scope=message)
                headers.append(self.header_name, request_id)
            await send(message)

        await self.app(scope, receive, send_with_request_id_header)
