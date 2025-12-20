from collections.abc import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from sqlalchemy.ext.asyncio import AsyncSession

from todo_api.auth.dependencies import AnonymousUser, get_user_from_session
from todo_api.core.database.dependencies import get_async_session
from todo_api.main import create_app
from todo_api.users.models import User


@pytest.fixture(autouse=True)
def isolated_tracer_provider():
    """Isolate tracer provider for each test

    - Save original provider
    - Create fresh provider for test
    - Restore original provider
    """
    original_provider = trace.get_tracer_provider()

    test_provider = TracerProvider()
    trace.set_tracer_provider(test_provider)

    yield test_provider

    trace.set_tracer_provider(original_provider)


@pytest_asyncio.fixture
async def app(
    auth_as: User | AnonymousUser | None, session: AsyncSession
) -> AsyncGenerator[FastAPI]:
    app_ = create_app()
    app_.dependency_overrides[get_async_session] = lambda: session
    if auth_as is not None:
        app_.dependency_overrides[get_user_from_session] = lambda: auth_as

    yield app_

    app_.dependency_overrides.pop(get_async_session)

    if auth_as is not None:
        app_.dependency_overrides.pop(get_user_from_session)


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[httpx.AsyncClient]:
    async with LifespanManager(app) as manager:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=manager.app), base_url="http://test"
        ) as client:
            yield client
