from collections.abc import AsyncGenerator
from typing import Any

import httpx
import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker

from todo_api.auth.dependencies import AnonymousUser, get_user_from_session
from todo_api.main import create_app
from todo_api.users.models import User


@pytest_asyncio.fixture
async def app(
    auth_as: User | AnonymousUser | None,
    sync_engine: Engine,
    sync_sessionmaker: sessionmaker[Session],
    sync_session: Session,
    async_engine: AsyncEngine,
    async_sessionmaker_: async_sessionmaker[AsyncSession],
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[FastAPI]:
    from todo_api.core.database.aa_config import alchemy_async, alchemy_sync

    def sync_get_session_from_request(*args: Any, **kwargs: Any) -> Session:
        return sync_session

    def async_get_session_from_request(*args: Any, **kwargs: Any) -> AsyncSession:
        return session

    monkeypatch.setattr(alchemy_sync, "_get_session_from_request", sync_get_session_from_request)
    monkeypatch.setattr(alchemy_async, "_get_session_from_request", async_get_session_from_request)

    app_ = create_app()

    if auth_as is not None:
        app_.dependency_overrides[get_user_from_session] = lambda: auth_as

    yield app_

    if auth_as is not None:
        app_.dependency_overrides.pop(get_user_from_session)


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[httpx.AsyncClient]:
    async with LifespanManager(app) as manager:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=manager.app), base_url="http://test"
        ) as client:
            yield client
