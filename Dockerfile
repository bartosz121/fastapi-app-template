ARG ENVIRONMENT=DEVELOPMENT

FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim AS builder

ARG ENVIRONMENT

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    if [ "${ENVIRONMENT}" = "PRODUCTION" ]; then \
    uv sync --locked --no-install-project --no-dev; \
    else \
    uv sync --locked --no-install-project --all-groups; \
    fi

COPY . /app

# `docker` and `.vscode` are in `.dockerignore`
# mark all tracked files inside docker/ and .vscode/ as unchanged
# without this, git will see the missing tracked files and mark the repository as dirty
# as a result, hatch-vcs/setuptools-scm would append a dirty tag (e.g., .postN.dev0) to the version
RUN git ls-files docker .vscode | xargs git update-index --assume-unchanged

RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "${ENVIRONMENT}" = "PRODUCTION" ]; then \
    uv sync --locked --no-dev; \
    else \
    uv sync --locked --all-groups; \
    fi


FROM python:3.14-slim-trixie AS final

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    libatomic1 \
    libpq5 && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 999 app \
    && useradd --system --gid 999 --uid 999 --create-home app

COPY --from=builder --chown=app:app /app /app

WORKDIR /app

RUN mkdir /tmp/prometheus \
    && chown app:app /tmp/prometheus

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER app

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["granian", "--loop", "uvloop", "--interface", "asgi", "--log-level", "info", "--access-log",  "--workers", "1", "--factory", "todo_api.main:create_app", "--host", "0.0.0.0", "--port", "8000"]
