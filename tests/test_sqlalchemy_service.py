# pyright: reportPrivateUsage=false
from unittest.mock import patch

import pytest
from sqlalchemy import Select, select
from sqlalchemy.dialects import sqlite
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, Mapped, mapped_column

from tests.fixtures.database import SaveModel
from todo_api.core.database.base import Model
from todo_api.core.exceptions import Conflict, NotFound
from todo_api.core.service.sqlalchemy import OrderBy, ServiceError, SQLAlchemyService

DIALECT = sqlite.dialect()


def assert_statement_equal(stmt1: Select, stmt2: Select):  # pyright: ignore[reportMissingTypeArgument, reportUnknownParameterType]
    compiled1 = str(stmt1.compile(dialect=DIALECT, compile_kwargs={"literal_binds": True}))
    compiled2 = str(stmt2.compile(dialect=DIALECT, compile_kwargs={"literal_binds": True}))
    assert compiled1 == compiled2


def assert_statement_not_equal(stmt1: Select, stmt2: Select):  # pyright: ignore[reportMissingTypeArgument, reportUnknownParameterType]
    compiled1 = str(stmt1.compile(dialect=DIALECT, compile_kwargs={"literal_binds": True}))
    compiled2 = str(stmt2.compile(dialect=DIALECT, compile_kwargs={"literal_binds": True}))
    assert compiled1 != compiled2


class Task(Model):
    __tablename__ = "test_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    description: Mapped[str | None] = mapped_column()
    priority: Mapped[int] = mapped_column(default=1)


class TaskService(SQLAlchemyService[Task, int]):
    model = Task


@pytest.fixture
def test_task():
    return Task(title="Test Task", description="Test Description", priority=1)


async def test_create(session: AsyncSession, test_task: Task):
    service = TaskService(session)

    created_task = await service.create(test_task)

    assert created_task.id is not None
    assert created_task.title == "Test Task"
    assert created_task.description == "Test Description"
    assert created_task.priority == 1


async def test_create_with_options(session: AsyncSession, test_task: Task):
    service = TaskService(session, auto_commit=True, auto_refresh=False, auto_expunge=True)

    created_task = await service.create(
        test_task, auto_commit=False, auto_refresh=True, auto_expunge=False
    )

    assert created_task.id is not None
    assert created_task.title == "Test Task"


async def test_get_one(session: AsyncSession, test_task: Task, save_model_fixture: SaveModel):
    await save_model_fixture(test_task)
    service = TaskService(session)

    task = await service.get_one(id=test_task.id)

    assert task.id == test_task.id
    assert task.title == test_task.title


async def test_get_one_not_found(session: AsyncSession):
    service = TaskService(session)

    with pytest.raises(NotFound):
        await service.get_one(id=999)


async def test_get_alias_for_get_one(
    session: AsyncSession, test_task: Task, save_model_fixture: SaveModel
):
    await save_model_fixture(test_task)
    service = TaskService(session)

    task = await service.get(id=test_task.id)

    assert task.id == test_task.id
    assert task.title == test_task.title


async def test_get_one_or_none_found(
    session: AsyncSession, test_task: Task, save_model_fixture: SaveModel
):
    await save_model_fixture(test_task)
    service = TaskService(session)

    task = await service.get_one_or_none(id=test_task.id)

    assert task is not None
    assert task.id == test_task.id


async def test_get_one_or_none_not_found(session: AsyncSession):
    service = TaskService(session)

    task = await service.get_one_or_none(id=999)

    assert task is None


async def test_list(session: AsyncSession, save_model_fixture: SaveModel):
    tasks = [
        Task(title="Task 1", priority=1),
        Task(title="Task 2", priority=2),
        Task(title="Task 3", priority=3),
    ]
    for task in tasks:
        await save_model_fixture(task)

    service = TaskService(session)

    result = await service.list()

    assert len(result) == 3
    assert all(isinstance(item, Task) for item in result)


async def test_list_with_filtering(session: AsyncSession, save_model_fixture: SaveModel):
    tasks = [
        Task(title="Task 1", priority=1),
        Task(title="Task 2", priority=2),
        Task(title="Task 3", priority=1),
    ]
    for task in tasks:
        await save_model_fixture(task)

    service = TaskService(session)

    result = await service.list(priority=1)

    assert len(result) == 2
    assert all(task.priority == 1 for task in result)


async def test_list_with_pagination(session: AsyncSession, save_model_fixture: SaveModel):
    tasks = [Task(title=f"Task {i}") for i in range(1, 6)]
    for task in tasks:
        await save_model_fixture(task)

    service = TaskService(session)

    result = await service.list(limit=2, offset=2)

    assert len(result) == 2


async def test_list_with_ordering(session: AsyncSession, save_model_fixture: SaveModel):
    tasks = [
        Task(title="Task A", priority=3),
        Task(title="Task B", priority=1),
        Task(title="Task C", priority=2),
    ]
    for task in tasks:
        await save_model_fixture(task)

    service = TaskService(session)

    result_asc = await service.list(order_by=OrderBy(field="priority", order="asc"))
    result_desc = await service.list(order_by=OrderBy(field="priority", order="desc"))

    assert result_asc[0].priority == 1
    assert result_asc[-1].priority == 3
    assert result_desc[0].priority == 3
    assert result_desc[-1].priority == 1


async def test_list_and_count(session: AsyncSession, save_model_fixture: SaveModel):
    tasks = [Task(title=f"Task {i}") for i in range(1, 6)]
    for task in tasks:
        await save_model_fixture(task)

    service = TaskService(session)

    items, count = await service.list_and_count(limit=2, offset=1)

    assert len(items) == 2
    assert count == 5


async def test_count(session: AsyncSession, save_model_fixture: SaveModel):
    tasks = [
        Task(title="Task 1", priority=1),
        Task(title="Task 2", priority=2),
        Task(title="Task 3", priority=1),
    ]
    for task in tasks:
        await save_model_fixture(task)

    service = TaskService(session)

    total_count = await service.count()
    filtered_count = await service.count(priority=1)

    assert total_count == 3
    assert filtered_count == 2


async def test_update(session: AsyncSession, test_task: Task, save_model_fixture: SaveModel):
    await save_model_fixture(test_task)
    service = TaskService(session)

    test_task.title = "Updated Task"
    test_task.priority = 5
    updated_task = await service.update(test_task)

    assert updated_task.title == "Updated Task"
    assert updated_task.priority == 5

    fresh_task = await service.get_one(id=test_task.id)
    assert fresh_task.title == "Updated Task"
    assert fresh_task.priority == 5


async def test_delete(session: AsyncSession, test_task: Task, save_model_fixture: SaveModel):
    await save_model_fixture(test_task)
    service = TaskService(session)

    deleted_task = await service.delete(test_task.id)

    assert deleted_task.id == test_task.id

    with pytest.raises(NotFound):
        await service.get_one(id=test_task.id)


async def test_exists(session: AsyncSession, test_task: Task, save_model_fixture: SaveModel):
    await save_model_fixture(test_task)
    service = TaskService(session)

    exists_true = await service.exists(id=test_task.id)
    exists_false = await service.exists(id=999)

    assert exists_true is True
    assert exists_false is False


async def test_sql_error_handling_integrity_error(session: AsyncSession):
    service = TaskService(session)

    # Mock session.execute to raise IntegrityError
    with patch.object(session, "execute", side_effect=IntegrityError("mock", "mock", "mock")):  # type: ignore
        with pytest.raises(Conflict):
            await service.get_one(id=1)


async def test_sql_error_handling_sqlalchemy_error(session: AsyncSession):
    service = TaskService(session)

    # Mock session.execute to raise SQLAlchemyError
    with patch.object(session, "execute", side_effect=SQLAlchemyError("mock error")):
        with pytest.raises(ServiceError):
            await service.get_one(id=1)


async def test_sql_error_handling_attribute_error(session: AsyncSession):
    service = TaskService(session)

    # Mock _get_model_id_attr to raise AttributeError
    with patch.object(service, "_get_model_id_attr", side_effect=AttributeError("mock error")):
        with pytest.raises(ServiceError):
            await service.count(id=1)


async def test_attach_to_session_invalid_strategy(session: AsyncSession, test_task: Task):
    service = TaskService(session)

    with pytest.raises(ServiceError):
        await service._attach_to_session(test_task, strategy="invalid")  # type: ignore


async def test_order_by_invalid_field(session: AsyncSession, save_model_fixture: SaveModel):
    tasks = [
        Task(title="Task A", priority=3),
        Task(title="Task B", priority=1),
    ]
    for task in tasks:
        await save_model_fixture(task)

    service = TaskService(session)

    result = await service.list(order_by=OrderBy(field="non_existent", order="asc"))

    assert len(result) == 2


async def test_where_from_kwargs_non_existent_field(session: AsyncSession):
    service = TaskService(session)
    statement = select(Task)

    result = service._where_from_kwargs(statement, non_existent_field="value")

    assert result is not None


async def test_where_from_kwargs_non_reserved(session: AsyncSession, test_task: Task):
    """Test filtering with non-reserved kwargs that are valid attributes."""
    service = TaskService(session)
    statement = select(Task)
    result = service._where_from_kwargs(statement, title="Test")

    assert "title" in str(result)


async def test_attach_to_session_add_strategy(session: AsyncSession, test_task: Task):
    """Test attaching a model to session with 'add' strategy."""
    service = TaskService(session)
    result = await service._attach_to_session(test_task, strategy="add")

    assert result is test_task
    assert test_task in session


async def test_attach_to_session_merge_strategy(session: AsyncSession, test_task: Task):
    """Test attaching a model to session with 'merge' strategy."""
    service = TaskService(session)

    session.add(test_task)
    await session.flush()

    assert test_task in session

    session.expunge(test_task)

    assert test_task not in session

    result = await service._attach_to_session(test_task, strategy="merge")

    assert result is not None
    assert result in session
    assert result is not test_task
    assert result.id == test_task.id


async def test_get_model_id_attr(session: AsyncSession):
    """Test that _get_model_id_attr returns the correct attribute."""
    service = TaskService(session)
    id_attr = service._get_model_id_attr()

    assert isinstance(id_attr, InstrumentedAttribute)
    assert id_attr.key == "id"


async def test_custom_model_id_attr_name(session: AsyncSession):
    """Test service with custom model_id_attr_name setting."""

    class CustomIdTask(Model):
        __tablename__ = "custom_id_tasks"
        item_id: Mapped[int] = mapped_column(primary_key=True)
        title: Mapped[str] = mapped_column()

    class CustomIdTaskService(SQLAlchemyService[CustomIdTask, int]):
        model = CustomIdTask
        model_id_attr_name = "item_id"

    service = CustomIdTaskService(session)
    id_attr = service._get_model_id_attr()

    assert id_attr.key == "item_id"


async def test_flush_or_commit_flush(session: AsyncSession):
    """Test _flush_or_commit when auto_commit is False."""
    service = TaskService(session)

    with patch.object(session, "flush") as mock_flush:
        await service._flush_or_commit(auto_commit=False)
        mock_flush.assert_called_once()


async def test_flush_or_commit_commit(session: AsyncSession):
    """Test _flush_or_commit when auto_commit is True."""
    service = TaskService(session)

    with patch.object(session, "commit") as mock_commit:
        await service._flush_or_commit(auto_commit=True)
        mock_commit.assert_called_once()


async def test_refresh_when_auto_refresh_true(session: AsyncSession, test_task: Task):
    """Test _refresh when auto_refresh is True."""
    service = TaskService(session)

    with patch.object(session, "refresh") as mock_refresh:
        await service._refresh(test_task, auto_refresh=True)
        mock_refresh.assert_called_once_with(test_task, attribute_names=None, with_for_update=None)


async def test_refresh_with_attribute_names(session: AsyncSession, test_task: Task):
    """Test _refresh with specific attribute_names."""
    service = TaskService(session)

    with patch.object(session, "refresh") as mock_refresh:
        await service._refresh(test_task, attribute_names=["title"], auto_refresh=True)
        mock_refresh.assert_called_once_with(
            test_task, attribute_names=["title"], with_for_update=None
        )


async def test_refresh_with_for_update(session: AsyncSession, test_task: Task):
    """Test _refresh with with_for_update flag."""
    service = TaskService(session)

    with patch.object(session, "refresh") as mock_refresh:
        await service._refresh(test_task, with_for_update=True, auto_refresh=True)
        mock_refresh.assert_called_once_with(test_task, attribute_names=None, with_for_update=True)


async def test_expunge_when_auto_expunge_false(session: AsyncSession, test_task: Task):
    """Test _expunge when auto_expunge is False."""
    service = TaskService(session)

    with patch.object(session, "expunge") as mock_expunge:
        service._expunge(test_task, auto_expunge=False)
        mock_expunge.assert_not_called()


async def test_get_statement_with_none(session: AsyncSession):
    """Test _get_statement when statement is None."""
    service = TaskService(session)
    result = service._get_statement(None)

    assert_statement_equal(result, service.statement)


async def test_get_statement_with_custom(session: AsyncSession):
    """Test _get_statement with a provided statement."""
    service = TaskService(session)
    custom_stmt = select(Task).where(Task.priority > 3)
    result = service._get_statement(custom_stmt)

    assert_statement_equal(result, custom_stmt)


async def test_update_conflict_error(session: AsyncSession, test_task: Task):
    """Test update when integrity error occurs."""
    service = TaskService(session)

    with patch.object(session, "merge", side_effect=IntegrityError("mock", "mock", "mock")):  # type: ignore
        # The update method catches IntegrityError and wraps it in ServiceError
        with pytest.raises(ServiceError):
            await service.update(test_task)


async def test_update_with_session_error(session: AsyncSession, test_task: Task):
    """Test update when a general SQLAlchemy error occurs."""
    service = TaskService(session)

    with patch.object(session, "merge", side_effect=SQLAlchemyError("mock error")):
        with pytest.raises(ServiceError):
            await service.update(test_task)


async def test_update_already_in_session(
    session: AsyncSession, test_task: Task, save_model_fixture: SaveModel
):
    """Test update when model is already in session."""
    await save_model_fixture(test_task)
    service = TaskService(session)

    with patch.object(session, "merge") as mock_merge:
        updated = await service.update(test_task)
        assert updated is test_task
        mock_merge.assert_not_called()


async def test_order_by_invalid_order(session: AsyncSession):
    """Test order_by with invalid order type."""

    service = TaskService(session)

    invalid_order_by = OrderBy(field="doesnt_exist", order="invalid")  # type: ignore

    await service.list(order_by=invalid_order_by)


async def test_list_with_multiple_filters(session: AsyncSession, save_model_fixture: SaveModel):
    """Test list with multiple filter criteria."""
    tasks = [
        Task(title="Common Title", description="Desc 1", priority=1),
        Task(title="Common Title", description="Desc 2", priority=2),
        Task(title="Different Title", description="Desc 3", priority=1),
    ]
    for task in tasks:
        await save_model_fixture(task)

    service = TaskService(session)
    result = await service.list(title="Common Title", priority=1)

    assert len(result) == 1
    assert result[0].description == "Desc 1"


async def test_sql_error_handler_unknown_exception(session: AsyncSession):
    """Test that non-SQLAlchemy exceptions are not caught by sql_error_handler."""
    service = TaskService(session)

    class CustomException(Exception):
        pass

    with patch.object(session, "execute", side_effect=CustomException("unexpected error")):
        with pytest.raises(CustomException):  # Should not be caught by sql_error_handler
            await service.get_one(id=1)


async def test_list_with_empty_result(session: AsyncSession):
    """Test list when no items match the criteria."""
    service = TaskService(session)

    result = await service.list(title="Non-existent Title")

    assert result == []


async def test_create_with_service_error(session: AsyncSession, test_task: Task):
    """Test create when an unexpected error occurs."""
    service = TaskService(session)

    # Simulate a situation that would cause ServiceError via SQLAlchemyError
    with patch.object(service, "_flush_or_commit", side_effect=SQLAlchemyError("unexpected")):
        with pytest.raises(ServiceError):
            await service.create(test_task)


async def test_list_and_count_empty_result(session: AsyncSession):
    """Test list_and_count when no items match the criteria."""
    service = TaskService(session)

    items, count = await service.list_and_count(title="Non-existent Title")

    assert items == []
    assert count == 0
