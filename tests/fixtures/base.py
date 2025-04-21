from collections.abc import AsyncGenerator

import httpx
import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from todo_api.auth.dependencies import get_user_from_jwt
from todo_api.auth.schemas import Anonymous
from todo_api.core.database.dependencies import get_async_session
from todo_api.main import create_app
from todo_api.users.models import User


@pytest_asyncio.fixture
async def app(auth_as: User | Anonymous | None, session: AsyncSession) -> AsyncGenerator[FastAPI]:
    app_ = create_app()
    app_.dependency_overrides[get_async_session] = lambda: session
    if auth_as is not None:
        app_.dependency_overrides[get_user_from_jwt] = lambda: auth_as

    yield app_

    app_.dependency_overrides.pop(get_async_session)

    if auth_as is not None:
        app_.dependency_overrides.pop(get_user_from_jwt)


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[httpx.AsyncClient]:
    async with LifespanManager(app) as manager:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=manager.app), base_url="http://test"
        ) as client:
            yield client
