ARG ENVIRONMENT=DEVELOPMENT

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    if [ "${ENVIRONMENT}" = "PRODUCTION" ]; then \
    uv sync --frozen --no-install-project --no-dev; \
    else \
    uv sync --frozen --no-install-project --all-groups; \
    fi

ADD . /app

RUN if [ "${ENVIRONMENT}" = "PRODUCTION" ]; then \
    uv sync --frozen --no-dev; \
    else \
    uv sync --frozen --all-groups; \
    fi


FROM python:3.13-slim-bookworm AS final

COPY --from=builder --chown=app:app /app /app

RUN mkdir /tmp/prometheus

ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "--workers", "4", "--factory", "todo_api.main:create_app", "--host", "0.0.0.0", "--port", "8000"]