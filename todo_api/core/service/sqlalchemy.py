from collections.abc import Iterable, Sequence
from contextlib import contextmanager
from typing import Any, Literal, NamedTuple, TypeVar

import structlog
from sqlalchemy import Select, asc, desc, func as sqla_func, over, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from todo_api.core.exceptions import Conflict, NotFound, TodoApiError

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class ServiceError(TodoApiError): ...


class OrderBy(NamedTuple):
    field: str
    order: Literal["asc", "desc"]


@contextmanager
def sql_error_handler():
    try:
        yield
    except IntegrityError as exc:
        logger.error(f"Database integrity error: {exc}", exc_info=True)
        raise Conflict() from exc
    except SQLAlchemyError as exc:
        logger.error(f"Database error during operation: {exc}", exc_info=True)
        raise ServiceError() from exc
    except AttributeError as exc:
        logger.error(f"Attribute error during service operation: {exc}", exc_info=True)
        raise ServiceError() from exc


T = TypeVar("T")
U = TypeVar("U")

RESERVED_KWARGS = {"offset", "limit", "order_by"}


class SQLAlchemyService[T, U]:
    model: type[T]
    model_id_attr_name: str = "id"

    def __init__(
        self,
        session: AsyncSession,
        *,
        statement: Select[tuple[T]] | None = None,
        auto_expunge: bool = False,
        auto_refresh: bool = True,
        auto_commit: bool = False,
    ) -> None:
        self.session = session

        self.statement = statement if statement is not None else select(self.model)
        self.auto_expunge = auto_expunge
        self.auto_refresh = auto_refresh
        self.auto_commit = auto_commit

    def _get_statement(self, statement: Select[tuple[T]] | None = None) -> Select[tuple[T]]:
        return statement if statement is not None else self.statement

    def _get_model_id_attr(self) -> InstrumentedAttribute[U]:
        return getattr(self.model, self.model_id_attr_name)

    async def _attach_to_session(self, model: T, strategy: Literal["add", "merge"] = "add") -> T:
        if strategy == "add":
            self.session.add(model)
            return model
        if strategy == "merge":
            return await self.session.merge(model)

        logger.error(
            f"Strategy must be 'add' or handled within async methods like 'update', found:{strategy!r}"
        )
        raise ServiceError()

    async def _flush_or_commit(self, auto_commit: bool | None = None) -> None:
        auto_commit_ = self.auto_commit if auto_commit is None else auto_commit
        if auto_commit_:
            await self.session.commit()
        else:
            await self.session.flush()

    async def _refresh(
        self,
        instance: T,
        attribute_names: Iterable[str] | None = None,
        *,
        auto_refresh: bool | None,
        with_for_update: bool | None = None,
    ) -> None:
        auto_refresh_ = self.auto_refresh if auto_refresh is None else auto_refresh
        if auto_refresh_:
            await self.session.refresh(
                instance,
                attribute_names=attribute_names,
                with_for_update=with_for_update,
            )

    def _expunge(self, instance: T, auto_expunge: bool | None = None) -> None:
        auto_expunge_ = self.auto_expunge if auto_expunge is None else auto_expunge
        if auto_expunge_:
            self.session.expunge(instance)

    def _where_from_kwargs(self, statement: Select[tuple[T]], **kwargs: Any) -> Select[tuple[T]]:
        stmt = statement
        for k, v in kwargs.items():
            if k not in RESERVED_KWARGS and hasattr(self.model, k):
                stmt = stmt.where(getattr(self.model, k) == v)
            elif k not in RESERVED_KWARGS:
                logger.warning(
                    f"Attempted to filter by non-existent attribute '{k}' on model {self.model.__name__}"
                )

        return stmt

    def _offset_from_kwargs(self, statement: Select[tuple[T]], **kwargs: Any) -> Select[tuple[T]]:
        if (offset := kwargs.get("offset")) is not None:
            return statement.offset(offset)
        return statement

    def _limit_from_kwargs(self, statement: Select[tuple[T]], **kwargs: Any) -> Select[tuple[T]]:
        if (limit := kwargs.get("limit")) is not None:
            return statement.limit(limit)
        return statement

    def _paginate_from_kwargs(
        self, statement: Select[tuple[T]], **kwargs: Any
    ) -> Select[tuple[T]]:
        stmt = self._offset_from_kwargs(statement, **kwargs)
        stmt = self._limit_from_kwargs(stmt, **kwargs)
        return stmt

    def _order_by_from_kwargs(
        self, statement: Select[tuple[T]], **kwargs: Any
    ) -> Select[tuple[T]]:
        order_by: OrderBy | None = kwargs.get("order_by")
        if isinstance(order_by, OrderBy):
            if hasattr(self.model, order_by.field):
                order_func = asc if order_by.order == "asc" else desc
                statement = statement.order_by(order_func(getattr(self.model, order_by.field)))
            else:
                logger.warning(
                    f"Attempted to order by non-existent attribute '{order_by.field}' on model {self.model.__name__}"
                )
        else:
            logger.warning(f"Invalid order_by type: {type(order_by)}. Expected OrderBy.")

        return statement

    def check_not_found(self, item: T | None) -> T:
        if item is None:
            msg = "No record found"
            raise NotFound(detail=msg)
        return item

    async def count(self, statement: Select[tuple[T]] | None = None, **kwargs: Any) -> int:
        with sql_error_handler():
            stmt = self._get_statement(statement)
            stmt = self._where_from_kwargs(stmt, **kwargs)

            count_statement = select(sqla_func.count()).select_from(
                stmt.with_only_columns(self._get_model_id_attr()).subquery()
            )

            result = await self.session.execute(count_statement)
            count = result.scalar_one_or_none()
            return count or 0

    async def create(
        self,
        data: T,
        *,
        auto_commit: bool | None = None,
        auto_refresh: bool | None = None,
        auto_expunge: bool | None = None,
    ) -> T:
        with sql_error_handler():
            instance = await self._attach_to_session(data, strategy="add")
            await self._flush_or_commit(auto_commit=auto_commit)
            await self._refresh(instance, auto_refresh=auto_refresh)
            self._expunge(instance, auto_expunge=auto_expunge)
            return instance

    async def delete(
        self,
        id: U,
        *,
        auto_commit: bool | None = None,
        auto_expunge: bool | None = None,
    ) -> T:
        with sql_error_handler():
            instance = await self.get_one(id=id, auto_expunge=False)
            await self.session.delete(instance)
            await self._flush_or_commit(auto_commit=auto_commit)
            self._expunge(instance, auto_expunge=auto_expunge)

            return instance

    async def exists(self, **kwargs: Any) -> bool:
        with sql_error_handler():
            stmt = self._get_statement()
            stmt = self._where_from_kwargs(stmt, **kwargs)

            stmt = stmt.with_only_columns(self._get_model_id_attr()).limit(1)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None

    async def get(
        self,
        *,
        statement: Select[tuple[T]] | None = None,
        auto_expunge: bool | None = None,
        **kwargs: Any,
    ) -> T:
        return await self.get_one(statement=statement, auto_expunge=auto_expunge, **kwargs)

    async def get_one(
        self,
        *,
        statement: Select[tuple[T]] | None = None,
        auto_expunge: bool | None = None,
        **kwargs: Any,
    ) -> T:
        with sql_error_handler():
            stmt = self._get_statement(statement)
            stmt = self._where_from_kwargs(stmt, **kwargs)

            result = await self.session.execute(stmt)
            instance = self.check_not_found(result.scalar_one_or_none())
            self._expunge(instance, auto_expunge=auto_expunge)
            return instance

    async def get_one_or_none(
        self,
        statement: Select[tuple[T]] | None = None,
        auto_expunge: bool | None = None,
        **kwargs: Any,
    ) -> T | None:
        with sql_error_handler():
            stmt = self._get_statement(statement)
            stmt = self._where_from_kwargs(stmt, **kwargs)

            result = await self.session.execute(stmt)
            instance = result.scalar_one_or_none()
            if instance:
                self._expunge(instance, auto_expunge=auto_expunge)
            return instance

    async def list(
        self,
        statement: Select[tuple[T]] | None = None,
        auto_expunge: bool | None = None,
        **kwargs: Any,
    ) -> Sequence[T]:
        with sql_error_handler():
            stmt = self._get_statement(statement)
            stmt = self._where_from_kwargs(stmt, **kwargs)
            stmt = self._paginate_from_kwargs(stmt, **kwargs)
            stmt = self._order_by_from_kwargs(stmt, **kwargs)

            result = await self.session.execute(stmt)
            items = list(result.scalars().all())
            for item in items:
                self._expunge(item, auto_expunge=auto_expunge)

            return items

    async def list_and_count(
        self,
        statement: Select[tuple[T]] | None = None,
        auto_expunge: bool | None = None,
        **kwargs: Any,
    ) -> tuple[Sequence[T], int]:
        with sql_error_handler():
            stmt = self._get_statement(statement)
            stmt = self._where_from_kwargs(stmt, **kwargs)
            stmt = self._order_by_from_kwargs(stmt, **kwargs)
            stmt = self._paginate_from_kwargs(stmt, **kwargs)

            stmt = stmt.add_columns(over(sqla_func.count()))

            result = await self.session.execute(stmt)
            rows = result.all()

            total_count = 0
            items: list[T] = []

            for i, row in enumerate(rows):
                instance, count_value = row
                self._expunge(instance, auto_expunge=auto_expunge)
                items.append(instance)
                if i == 0:
                    total_count = count_value

            return items, total_count

    async def update(
        self,
        data: T,
        *,
        auto_commit: bool | None = None,
        auto_refresh: bool | None = None,
        auto_expunge: bool | None = None,
        attribute_names: Iterable[str] | None = None,
        with_for_update: bool | None = None,
    ) -> T:
        with sql_error_handler():
            if data not in self.session:
                try:
                    instance = await self.session.merge(data)
                except Exception as exc:
                    logger.error(f"Failed to merge instance for update: {exc}", exc_info=True)
                    raise ServiceError() from exc

            else:
                instance = data

            await self._flush_or_commit(auto_commit=auto_commit)
            await self._refresh(
                instance,
                attribute_names=attribute_names,
                with_for_update=with_for_update,
                auto_refresh=auto_refresh,
            )
            self._expunge(instance, auto_expunge=auto_expunge)
            return instance
