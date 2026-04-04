# pyright: reportUnknownVariableType=false, reportMissingTypeStubs=false
import os
from collections.abc import AsyncGenerator, Callable, Coroutine, Iterator
from contextlib import contextmanager
from typing import Any
from uuid import uuid4

import pytest_asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Connection
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from todo_api.core.config import settings
from todo_api.core.database.base import Model


def _build_postgres_dsn(database_name: str) -> str:
    return URL.create(
        "postgresql+psycopg",
        username=settings.DB_USER,
        password=settings.DB_PASSWORD.get_secret_value(),
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=database_name,
    ).render_as_string(hide_password=False)


def _get_admin_database_dsn() -> str:
    return _build_postgres_dsn("postgres")


def _get_template_database_name() -> str:
    """Return the per-worker template database name configured in conftest.py"""
    return os.environ["DB_TEMPLATE_DATABASE"]


@contextmanager
def _admin_connection() -> Iterator[Connection]:
    """`admin` is the connection used for database-level Postgres commands"""
    engine = create_engine(_get_admin_database_dsn(), isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            yield connection
    finally:
        engine.dispose()


def _database_exists(database_name: str) -> bool:
    with _admin_connection() as connection:
        query = text("SELECT 1 FROM pg_database WHERE datname = :database_name")
        return connection.execute(query, {"database_name": database_name}).scalar() == 1


def _create_database(database_name: str) -> None:
    with _admin_connection() as connection:
        connection.exec_driver_sql(f'CREATE DATABASE "{database_name}"')


def _create_database_from_template(database_name: str, template_database_name: str) -> None:
    with _admin_connection() as connection:
        connection.exec_driver_sql(
            " ".join(
                (
                    f'CREATE DATABASE "{database_name}"',
                    f'TEMPLATE "{template_database_name}"',
                )
            )
        )


def _drop_database(database_name: str) -> None:
    with _admin_connection() as connection:
        connection.exec_driver_sql(f'DROP DATABASE IF EXISTS "{database_name}" WITH (FORCE)')


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def template_database() -> AsyncGenerator[str]:
    template_database_name = _get_template_database_name()

    if _database_exists(template_database_name):
        _drop_database(template_database_name)

    _create_database(template_database_name)

    template_engine = create_engine(_build_postgres_dsn(template_database_name))
    try:
        with template_engine.begin() as connection:
            Model.metadata.create_all(bind=connection)
    finally:
        template_engine.dispose()

    try:
        yield template_database_name
    finally:
        _drop_database(template_database_name)


@pytest_asyncio.fixture
async def engine(template_database: str) -> AsyncGenerator[AsyncEngine]:
    """Create a fresh cloned database and async engine"""
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
    database_name = f"test_db_{worker_id}_{uuid4().hex}".lower()

    _create_database_from_template(database_name, template_database)
    test_engine = create_async_engine(_build_postgres_dsn(database_name))

    try:
        yield test_engine
    finally:
        await test_engine.dispose()
        _drop_database(database_name)


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    """Provide a session bound to the test's dedicated cloned database"""
    test_session = AsyncSession(bind=engine, expire_on_commit=False)

    yield test_session

    await test_session.close()


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


@pytest_asyncio.fixture
async def seed_db(engine: AsyncEngine) -> AsyncGenerator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)
        await conn.run_sync(Model.metadata.create_all)

        # Add data here

    yield
