import pytest
from sqlalchemy import ForeignKey, String, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from todo_api.core.database.base import Model
from todo_api.core.exceptions import NotFound
from todo_api.core.service.sqlalchemy import SQLAlchemyService
from todo_api.users.models import User


@pytest.fixture
async def service(session: AsyncSession) -> SQLAlchemyService:
    return SQLAlchemyService(session)


@pytest.fixture
async def seeded_users(session: AsyncSession) -> list[User]:
    users = [
        User(username="user1", hashed_password="pw1"),
        User(username="user2", hashed_password="pw2"),
    ]
    session.add_all(users)
    await session.commit()
    for u in users:
        await session.refresh(u)
    return users


async def test_execute_one_success(service: SQLAlchemyService, seeded_users: list[User]):
    user = seeded_users[0]
    stmt = select(User).where(User.id == user.id)
    result = await service.execute_one(stmt)
    assert result.id == user.id
    assert result.username == "user1"


async def test_execute_one_not_found(service: SQLAlchemyService):
    stmt = select(User).where(User.id == 999)
    with pytest.raises(NotFound):
        await service.execute_one(stmt)


async def test_execute_one_or_none_success(service: SQLAlchemyService, seeded_users: list[User]):
    user = seeded_users[0]
    stmt = select(User).where(User.id == user.id)
    result = await service.execute_one_or_none(stmt)
    assert result is not None
    assert result.id == user.id


async def test_execute_one_or_none_none(service: SQLAlchemyService):
    stmt = select(User).where(User.id == 999)
    result = await service.execute_one_or_none(stmt)
    assert result is None


async def test_execute_list_success(service: SQLAlchemyService, seeded_users: list[User]):
    stmt = select(User).order_by(User.username.asc())
    results = await service.execute_list(stmt)
    assert len(results) == 2
    assert results[0].username == "user1"
    assert results[1].username == "user2"


async def test_execute_rows_multi_column(service: SQLAlchemyService, seeded_users: list[User]):
    stmt = select(User.id, User.username).order_by(User.username.asc())
    results = await service.execute_rows(stmt)
    assert len(results) == 2
    assert results[0][1] == "user1"
    assert results[1][1] == "user2"


async def test_execute_list_and_count_success(
    service: SQLAlchemyService, seeded_users: list[User]
):
    stmt = select(User).order_by(User.username.asc())
    items, count = await service.execute_list_and_count(stmt)
    assert count == 2
    assert len(items) == 2
    assert items[0].username == "user1"


async def test_execute_rows_cte(service: SQLAlchemyService, seeded_users: list[User]):
    cte = select(User.id, User.username).where(User.username == "user1").cte("user_cte")
    stmt = select(cte.c.id, cte.c.username)
    results = await service.execute_rows(stmt)
    assert len(results) == 1
    assert results[0][1] == "user1"


class Department(Model):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    employees: Mapped[list[Employee]] = relationship(back_populates="department")


class Employee(Model):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    salary: Mapped[int] = mapped_column()
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    department: Mapped[Department] = relationship(back_populates="employees")


@pytest.fixture
async def seeded_data(session: AsyncSession):
    dept1 = Department(name="Engineering")
    dept2 = Department(name="Marketing")
    session.add_all([dept1, dept2])
    await session.flush()

    emp1 = Employee(name="Alice", salary=100000, department_id=dept1.id)
    emp2 = Employee(name="Bob", salary=80000, department_id=dept1.id)
    emp3 = Employee(name="Charlie", salary=90000, department_id=dept2.id)
    session.add_all([emp1, emp2, emp3])

    await session.commit()
    return dept1, dept2


async def test_execute_rows_raw_sql(service: SQLAlchemyService, seeded_users: list[User]):
    stmt = select(text("id, username")).select_from(text("users")).order_by(text("username"))
    results = await service.execute_rows(stmt)

    assert len(results) == 2
    assert results[0][1] == "user1"  # type: ignore
    assert results[1][1] == "user2"  # type: ignore


async def test_execute_rows_complex_join(
    service: SQLAlchemyService, seeded_data: tuple[Department, Department]
):
    stmt = (
        select(Employee.name, Department.name.label("dept_name"))
        .join(Department)
        .order_by(Employee.name)
    )
    results = await service.execute_rows(stmt)

    assert len(results) == 3
    assert results[0][0] == "Alice"
    assert results[0][1] == "Engineering"
    assert results[2][0] == "Charlie"
    assert results[2][1] == "Marketing"


async def test_execute_rows_calculated_columns(
    service: SQLAlchemyService, seeded_data: tuple[Department, Department]
):
    stmt = (
        select(
            Employee.name,
            (Employee.salary * 1.1).label("increased_salary"),
            (Employee.name + " (" + Department.name + ")").label("display_name"),
        )
        .join(Department)
        .where(Employee.name == "Alice")
    )

    results = await service.execute_rows(stmt)
    assert len(results) == 1
    assert results[0][0] == "Alice"
    assert abs(float(results[0][1]) - 110000.0) < 1e-9
    assert results[0][2] == "Alice (Engineering)"


async def test_execute_rows_aggregation(
    service: SQLAlchemyService, seeded_data: tuple[Department, Department]
):
    from sqlalchemy import func

    stmt = (
        select(Department.name, func.avg(Employee.salary).label("avg_salary"))
        .join(Employee)
        .group_by(Department.name)
        .order_by(Department.name)
    )

    results = await service.execute_rows(stmt)
    assert len(results) == 2
    assert results[0][0] == "Engineering"
    assert results[0][1] == 90000.0  # (100k + 80k) / 2
    assert results[1][0] == "Marketing"
    assert results[1][1] == 90000.0
