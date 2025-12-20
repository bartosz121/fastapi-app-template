from opentelemetry.instrumentation.sqlalchemy import (  # pyright: ignore[reportMissingTypeStubs]
    SQLAlchemyInstrumentor,
)
from sqlalchemy import Engine, MetaData, create_engine as _create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine as _create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from todo_api.core.config import settings

metadata_ = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_N_label)s",
        "uq": "%(table_name)s_%(column_0_N_name)s_key",
        "ck": "%(table_name)s_%(constraint_name)s_check",
        "fk": "%(table_name)s_%(column_0_N_name)s_fkey",
        "pk": "%(table_name)s_pkey",
    }
)


def create_engine(
    *,
    dsn: str,
    app_name: str | None = None,
    pool_size: int = 5,
    pool_recycle: int = 3600,
    pool_pre_ping: bool = True,
    debug: bool = False,
) -> Engine:
    return _create_engine(
        dsn,
        echo=debug,
        pool_size=pool_size,
        pool_recycle=pool_recycle,
        pool_pre_ping=pool_pre_ping,
        connect_args={"server_settings": {"application_name": app_name}} if app_name else {},
    )


def create_async_engine(
    *,
    dsn: str,
    app_name: str | None = None,
    pool_size: int = 5,
    pool_recycle: int = 3600,
    pool_pre_ping: bool = True,
    debug: bool = False,
) -> AsyncEngine:
    return _create_async_engine(
        dsn,
        echo=debug,
        pool_size=pool_size,
        pool_recycle=pool_recycle,
        pool_pre_ping=pool_pre_ping,
        connect_args={"server_settings": {"application_name": app_name}} if app_name else {},
    )


engine = create_engine(dsn=settings.get_sqlite_dsn(), debug=settings.ENVIRONMENT.is_qa)
async_engine = create_async_engine(
    dsn=settings.get_sqlite_dsn(driver="aiosqlite"), debug=settings.ENVIRONMENT.is_qa
)

SQLAlchemyInstrumentor().instrument(engines=[engine, async_engine.sync_engine])

SyncSessionMaker = sessionmaker(engine, expire_on_commit=False)
AsyncSessionMaker = async_sessionmaker(async_engine, expire_on_commit=False)


class Model(DeclarativeBase):
    __abstract__ = True

    _eq_attr_name: str = "id"

    metadata = metadata_

    def __eq__(self, value: object) -> bool:
        self_eq_attr_val = getattr(self, self._eq_attr_name)
        value_eq_attr_val = getattr(value, self._eq_attr_name)

        if self_eq_attr_val is None or value_eq_attr_val is None:
            return False

        return isinstance(value, self.__class__) and self_eq_attr_val == value_eq_attr_val

    def __repr__(self) -> str:
        id_value = getattr(self, self._eq_attr_name)
        return f"{self.__class__.__name__}({self._eq_attr_name}={id_value!r})"
