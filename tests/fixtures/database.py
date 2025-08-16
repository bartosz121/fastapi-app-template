# pyright: reportUnknownVariableType=false, reportMissingTypeStubs=false
from collections.abc import AsyncGenerator, Callable, Coroutine, Generator
from typing import Any

import pytest
import pytest_asyncio
from advanced_alchemy.base import AdvancedDeclarativeBase, orm_registry
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import (
    create_database,
    database_exists,
    drop_database,
)

from todo_api.core.config import settings


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def initialize_test_database():
    sync_db_dsn = settings.get_sqlite_dsn()

    if database_exists(sync_db_dsn):
        drop_database(sync_db_dsn)

    create_database(sync_db_dsn)

    async_db_dsn = settings.get_sqlite_dsn(driver="aiosqlite")
    engine = create_async_engine(async_db_dsn)

    async with engine.begin() as conn:
        await conn.run_sync(orm_registry.metadata.create_all)
    await engine.dispose()

    yield

    drop_database(sync_db_dsn)


@pytest.fixture
def sync_engine() -> Engine:
    db_dsn = settings.get_sqlite_dsn()
    engine = create_engine(db_dsn, echo=False, poolclass=NullPool)
    return engine


@pytest.fixture
def sync_sessionmaker(sync_engine: Engine) -> Generator[sessionmaker[Session]]:
    yield sessionmaker(sync_engine)


@pytest.fixture(scope="function")
def sync_session(sync_sessionmaker: sessionmaker[Session]) -> Generator[Session]:
    with sync_sessionmaker() as session:
        yield session

        session.rollback()


@pytest_asyncio.fixture
async def async_engine() -> AsyncEngine:
    async_db_dsn = settings.get_sqlite_dsn(driver="aiosqlite")
    engine = create_async_engine(async_db_dsn, echo=False, poolclass=NullPool)
    return engine


@pytest_asyncio.fixture
async def async_sessionmaker_(
    async_engine: AsyncEngine,
) -> AsyncGenerator[async_sessionmaker[AsyncSession]]:
    yield async_sessionmaker[AsyncSession](bind=async_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def session(
    async_sessionmaker_: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession]:
    async with async_sessionmaker_() as session:
        yield session


SaveModel = Callable[[AdvancedDeclarativeBase], Coroutine[Any, Any, None]]


@pytest_asyncio.fixture
async def save_model_fixture(session: AsyncSession) -> SaveModel:
    def _save_model_fixture_factory(session: AsyncSession):
        async def _save_model_fixture(model: AdvancedDeclarativeBase):
            session.add(model)
            await session.flush()

        return _save_model_fixture

    return _save_model_fixture_factory(session)


@pytest_asyncio.fixture(autouse=True)
async def seed_db(async_engine: AsyncEngine, session: AsyncSession) -> AsyncGenerator[None]:
    metadata = orm_registry.metadata

    async with async_engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)

        # Add data here

    yield
