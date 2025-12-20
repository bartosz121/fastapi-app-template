import structlog
from opentelemetry import trace
from starlette.types import ASGIApp, Receive, Scope, Send

from todo_api.core.middleware.request_id import request_id_ctx


class LoggingMiddleware:
    app: ASGIApp

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    def _bind_opentelemetry_context(self, scope: Scope) -> None:
        """
        Bind OpenTelemetry trace context to structlog for the current request.

        Granian access log can't use contextvars, this prevents
        structlog filters from accessing span_id and trace_id.

        To ensure access logs (and any other logs after the response is sent)
        have trace correlation, we capture the span context here while it's
        still active and bind it to structlog.contextvars. These bindings
        persist even after the span context is destroyed.

        Reference: https://github.com/emmett-framework/granian/issues/715
        """
        # Get trace context while span is active
        span = trace.get_current_span()

        if not span.is_recording():
            structlog.contextvars.bind_contextvars(
                span_id=None,
                trace_id=None,
                parent_span_id=None,
            )
            return

        ctx = span.get_span_context()
        parent = getattr(span, "parent", None)

        trace_id = format(ctx.trace_id, "032x") if ctx.trace_id else None
        span_id = format(ctx.span_id, "016x") if ctx.span_id else None
        parent_span_id = None if not parent else format(parent.span_id, "016x")

        structlog.contextvars.bind_contextvars(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
        )

    def _bind_request_context(self, scope: Scope) -> None:
        structlog.contextvars.bind_contextvars(
            user_id=None,
            request_id=request_id_ctx.get(),
            method=scope["method"],
            path=scope["path"],
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        structlog.contextvars.clear_contextvars()
        self._bind_request_context(scope)
        self._bind_opentelemetry_context(scope)

        await self.app(scope, receive, send)
