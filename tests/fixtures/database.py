# pyright: reportUnknownVariableType=false, reportMissingTypeStubs=false
from collections.abc import AsyncGenerator, Callable, Coroutine
from typing import Any

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy_utils import (
    create_database,
    database_exists,
    drop_database,
)

from todo_api.core.config import settings
from todo_api.core.database.base import Model


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine() -> AsyncEngine:
    async_db_dsn = settings.get_sqlite_dsn(driver="aiosqlite")
    engine = create_async_engine(async_db_dsn)
    return engine


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def initialize_test_database(engine: AsyncEngine):
    sync_db_dsn = settings.get_sqlite_dsn()

    if database_exists(sync_db_dsn):
        drop_database(sync_db_dsn)

    create_database(sync_db_dsn)

    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
    await engine.dispose()

    yield

    drop_database(sync_db_dsn)


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    async_db_dsn = settings.get_sqlite_dsn(driver="aiosqlite")
    engine = create_async_engine(async_db_dsn, echo=True)
    conn = await engine.connect()
    transaction = await conn.begin()

    session = AsyncSession(bind=conn, expire_on_commit=False)

    yield session

    await transaction.rollback()
    await conn.close()
    await engine.dispose()


SaveModel = Callable[[Model], Coroutine[Any, Any, None]]


@pytest_asyncio.fixture
async def save_model_fixture(session: AsyncSession) -> SaveModel:
    def _save_model_fixture_factory(
        session: AsyncSession,
    ) -> Callable[[Model], Coroutine[None, None, None]]:
        async def _save_model_fixture(model: Model) -> None:
            session.add(model)
            await session.commit()

        return _save_model_fixture

    return _save_model_fixture_factory(session)


@pytest_asyncio.fixture(autouse=True)
async def seed_db(engine: AsyncEngine, session: AsyncSession) -> AsyncGenerator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)

        await conn.run_sync(Model.metadata.create_all)

        # Add data here

    yield
