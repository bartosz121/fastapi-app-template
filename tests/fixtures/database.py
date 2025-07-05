# pyright: reportUnknownVariableType=false, reportMissingTypeStubs=false
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy_utils import (
    create_database,
    database_exists,
    drop_database,
)

from todo_api.core.config import settings
from todo_api.core.database.base import Model


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def initialize_test_database():
    sync_db_dsn = settings.get_sqlite_dsn()

    if database_exists(sync_db_dsn):
        drop_database(sync_db_dsn)

    create_database(sync_db_dsn)

    async_db_dsn = settings.get_sqlite_dsn(driver="aiosqlite")
    engine = create_async_engine(async_db_dsn)

    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
    await engine.dispose()

    yield

    drop_database(sync_db_dsn)


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
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
    def _save_model_fixture_factory(session: AsyncSession):
        async def _save_model_fixture(model: Model):
            session.add(model)
            await session.commit()

        return _save_model_fixture

    return _save_model_fixture_factory(session)
