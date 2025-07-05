import asyncio

import httpx
import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fixtures.auth import AuthenticateAs
from tests.fixtures.database import SaveModel
from tests.fixtures.objects import create_user
from todo_api.auth.schemas import Anonymous
from todo_api.core.exceptions import Codes
from todo_api.todos.models import Todo
from todo_api.users.models import User


@pytest.mark.auth(AuthenticateAs(type_="user"))
async def test_create_todo_success(
    auth_as: User, client: httpx.AsyncClient, session: AsyncSession
):
    payload = {"title": "Test Todo", "description": "Test Description", "isCompleted": False}
    response = await client.post("/api/v1/todos", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["isCompleted"] is False
    assert "id" in data
    assert "createdAt" in data
    assert "updatedAt" in data

    db_todo = await session.get(Todo, data["id"])
    assert db_todo is not None
    assert db_todo.title == payload["title"]
    assert db_todo.description == payload["description"]
    assert db_todo.is_completed == payload["isCompleted"]
    assert db_todo.user_id == auth_as.id


async def test_create_todo_unauthenticated(client: httpx.AsyncClient):
    """Test creating a todo fails when not authenticated"""
    payload = {"title": "Test Todo", "description": "Test Description"}
    response = await client.post("/api/v1/todos", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.auth(AuthenticateAs(type_="user"))
async def test_get_user_todos_success(
    auth_as: User, client: httpx.AsyncClient, save_model_fixture: SaveModel
):
    """Test successfully retrieving todos for the authenticated user"""
    todo1 = Todo(user_id=auth_as.id, title="Todo 1", description="Desc 1")
    todo2 = Todo(user_id=auth_as.id, title="Todo 2", description="Desc 2", is_completed=True)
    await save_model_fixture(todo1)
    await save_model_fixture(todo2)

    other_user = await create_user(
        save_model_fixture,
        username="user2",
    )
    other_todo = Todo(user_id=other_user.id, title="Other User Todo", description="Desc Other")
    await save_model_fixture(other_todo)

    response = await client.get("/api/v1/todos/me")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["totalCount"] == 2
    assert data["page"] == 1
    assert len(data["items"]) == 2

    returned_titles = {item["title"] for item in data["items"]}
    assert returned_titles == {"Todo 1", "Todo 2"}


@pytest.mark.auth(AuthenticateAs(type_="user"))
async def test_get_user_todos_pagination(
    auth_as: User, client: httpx.AsyncClient, save_model_fixture: SaveModel
):
    """Test pagination for user's todos"""
    for i in range(3):
        await save_model_fixture(Todo(user_id=auth_as.id, title=f"Todo {i + 1}"))

    response = await client.get("/api/v1/todos/me?page=1&size=2")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["totalCount"] == 3
    assert data["page"] == 1
    assert data["size"] == 2
    assert len(data["items"]) == 2
    assert data["pages"] == 2

    response = await client.get("/api/v1/todos/me?page=2&size=2")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["totalCount"] == 3
    assert data["page"] == 2
    assert data["size"] == 2
    assert len(data["items"]) == 1
    assert data["pages"] == 2


@pytest.mark.auth(AuthenticateAs(type_="user"))
async def test_get_user_todos_sorting(
    auth_as: User, client: httpx.AsyncClient, save_model_fixture: SaveModel
):
    """Test sorting for user's todos"""
    todo1 = Todo(user_id=auth_as.id, title="First")
    await save_model_fixture(todo1)

    await asyncio.sleep(0.1)

    todo2 = Todo(user_id=auth_as.id, title="Second")
    await save_model_fixture(todo2)

    response = await client.get("/api/v1/todos/me")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] == "First"
    assert data["items"][1]["title"] == "Second"

    response = await client.get("/api/v1/todos/me?orderBy=createdAt.desc")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] == "Second"
    assert data["items"][1]["title"] == "First"

    response = await client.get("/api/v1/todos/me?orderBy=updatedAt.desc")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] == "Second"
    assert data["items"][1]["title"] == "First"


async def test_get_user_todos_unauthenticated(client: httpx.AsyncClient, auth_as: Anonymous):
    """Test getting user todos fails when effectively unauthenticated"""
    response = await client.get("/api/v1/todos/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.auth(AuthenticateAs(type_="user"))
async def test_get_todo_by_id_success(
    auth_as: User, client: httpx.AsyncClient, save_model_fixture: SaveModel
):
    """Test successfully retrieving a specific todo by its ID"""
    todo = Todo(user_id=auth_as.id, title="Specific Todo")
    await save_model_fixture(todo)

    response = await client.get(f"/api/v1/todos/{todo.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == todo.id
    assert data["title"] == todo.title


@pytest.mark.auth(AuthenticateAs(type_="user"))
async def test_get_todo_by_id_not_found(auth_as: User, client: httpx.AsyncClient):
    """Test retrieving a todo by ID fails when the ID does not exist (authenticated)"""
    non_existent_id = 9999
    response = await client.get(f"/api/v1/todos/{non_existent_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.auth(AuthenticateAs(type_="user", username="requester"))
async def test_get_todo_by_id_forbidden(
    auth_as: User, client: httpx.AsyncClient, save_model_fixture: SaveModel
):
    """Test retrieving a todo by ID fails when the todo belongs to another user"""
    owner_user = await create_user(save_model_fixture, username="owner")

    todo = Todo(user_id=owner_user.id, title="Owner's Todo")
    await save_model_fixture(todo)

    response = await client.get(f"/api/v1/todos/{todo.id}")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"]["code"] == Codes.NOT_OWNER


async def test_get_todo_by_id_unauthenticated(
    client: httpx.AsyncClient, save_model_fixture: SaveModel, auth_as: Anonymous
):
    owner_user = await create_user(save_model_fixture, username="owner_for_unauth_test")
    todo = Todo(user_id=owner_user.id, title="Auth Test Todo")
    await save_model_fixture(todo)

    response = await client.get(f"/api/v1/todos/{todo.id}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.auth(AuthenticateAs(type_="user"))
async def test_update_todo_success(
    auth_as: User, client: httpx.AsyncClient, save_model_fixture: SaveModel, session: AsyncSession
):
    """Test successfully updating a todo item"""
    todo = Todo(user_id=auth_as.id, title="Original Title", description="Original Desc")
    await save_model_fixture(todo)

    update_payload = {"title": "Updated Title", "isCompleted": True}
    response = await client.put(f"/api/v1/todos/{todo.id}", json=update_payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == todo.id
    assert data["title"] == update_payload["title"]
    assert data["description"] == todo.description
    assert data["isCompleted"] == update_payload["isCompleted"]
    assert data["createdAt"] is not None

    await session.refresh(todo)
    assert todo.updated_at is not None
    assert todo.updated_at >= todo.created_at


@pytest.mark.auth(AuthenticateAs(type_="user"))
async def test_update_todo_not_found(auth_as: User, client: httpx.AsyncClient):
    """Test updating a todo fails when the ID does not exist (authenticated)"""
    non_existent_id = 9999
    update_payload = {"title": "Updated Title", "isCompleted": True}

    response = await client.put(f"/api/v1/todos/{non_existent_id}", json=update_payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.auth(AuthenticateAs(type_="user", username="updater"))
async def test_update_todo_forbidden(
    auth_as: User, client: httpx.AsyncClient, save_model_fixture: SaveModel
):
    """Test updating a todo fails when the todo belongs to another user"""
    owner_user = await create_user(save_model_fixture, username="owner_update")

    todo = Todo(user_id=owner_user.id, title="Owner's Update Todo")
    await save_model_fixture(todo)

    update_payload = {"title": "Attempted Update Title", "isCompleted": True}
    response = await client.put(f"/api/v1/todos/{todo.id}", json=update_payload)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"]["code"] == Codes.NOT_OWNER


async def test_update_todo_unauthenticated(
    client: httpx.AsyncClient,
    save_model_fixture: SaveModel,
    auth_as: Anonymous,
):
    """Test updating a todo fails when not authenticated"""
    assert isinstance(auth_as, Anonymous)
    owner_user = await create_user(save_model_fixture, username="owner_for_unauth_update")
    todo = Todo(user_id=owner_user.id, title="Update Auth Test")
    await save_model_fixture(todo)

    update_payload = {"title": "Updated Title", "isCompleted": True}
    response = await client.put(f"/api/v1/todos/{todo.id}", json=update_payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.auth(AuthenticateAs(type_="user"))
async def test_delete_todo_success(
    auth_as: User, client: httpx.AsyncClient, save_model_fixture: SaveModel, session: AsyncSession
):
    """Test successfully deleting a todo item"""
    todo = Todo(user_id=auth_as.id, title="To Be Deleted")
    await save_model_fixture(todo)
    todo_id = todo.id

    response = await client.delete(f"/api/v1/todos/{todo_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    db_todo = await session.get(Todo, todo_id)
    assert db_todo is None


@pytest.mark.auth(AuthenticateAs(type_="user"))
async def test_delete_todo_not_found(auth_as: User, client: httpx.AsyncClient):
    """Test deleting a todo fails when the ID does not exist (authenticated)"""
    non_existent_id = 9999

    response = await client.delete(f"/api/v1/todos/{non_existent_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.auth(AuthenticateAs(type_="user", username="deleter"))
async def test_delete_todo_forbidden(
    auth_as: User, client: httpx.AsyncClient, save_model_fixture: SaveModel, session: AsyncSession
):
    """Test deleting a todo fails when the todo belongs to another user"""
    owner_user = await create_user(save_model_fixture, username="owner_delete")
    assert owner_user.id != auth_as.id

    todo = Todo(user_id=owner_user.id, title="Owner's Delete Todo")
    await save_model_fixture(todo)
    todo_id = todo.id

    response = await client.delete(f"/api/v1/todos/{todo_id}")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"]["code"] == Codes.NOT_OWNER

    db_todo = await session.get(Todo, todo_id)
    assert db_todo is not None


async def test_delete_todo_unauthenticated(
    client: httpx.AsyncClient,
    save_model_fixture: SaveModel,
    session: AsyncSession,
    auth_as: User | Anonymous,
):
    """Test deleting a todo fails when not authenticated"""
    owner_user = await create_user(save_model_fixture, username="owner_for_unauth_delete")
    todo = Todo(user_id=owner_user.id, title="Delete Auth Test")
    await save_model_fixture(todo)
    await session.refresh(todo)
    todo_id = todo.id

    response = await client.delete(f"/api/v1/todos/{todo_id}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    db_todo = await session.get(Todo, todo_id)
    assert db_todo is not None
