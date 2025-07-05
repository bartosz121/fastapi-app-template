"""
This module provides a flexible authentication testing fixture for pytest

Credits: https://github.com/polarsource

The core of this system is the `auth_as` fixture, which is dynamically
parameterized by the `pytest_generate_tests` hook. This allows tests to be
run against different authentication states (e.g., anonymous, authenticated user)
by simply applying a `@pytest.mark.auth` marker.

How it works:

1.  **`AuthenticateAs` Dataclass:** This dataclass defines the desired
    authentication state for a test. It can specify the user type (`user`,
    `anonymous`, or `dont_override`), and optionally a username and password.

2.  **`@pytest.mark.auth` Marker:** Tests are marked with this to specify the
    authentication state they should run in. For example:

    ```python
    @pytest.mark.auth(AuthenticateAs(type_="user"))
    def test_some_feature(auth_as: User, client: httpx.AsyncClient):
        ...
    ```

3.  **`pytest_generate_tests` Hook:** This hook intercepts the test generation
    process. If a test uses the `auth_as` fixture, it looks for a `@pytest.mark.auth`
    marker. Based on the marker's arguments, it generates parameterized versions
    of the test for each specified authentication state.

4.  **`auth_as` Fixture:** This fixture receives the `AuthenticateAs` object from
    `pytest_generate_tests`. It then creates the appropriate user in the database
    (or returns an `Anonymous` object) and makes it available to the test function.
"""

import uuid
from dataclasses import dataclass
from typing import Any, Literal

import pytest
import pytest_asyncio

from tests.fixtures.database import SaveModel
from todo_api.auth.schemas import Anonymous
from todo_api.users import security
from todo_api.users.models import User
from todo_api.users.security import get_password_hash


@dataclass
class AuthenticateAs:
    type_: Literal["user", "anonymous", "dont_override"] = "anonymous"
    username: str | None = None
    password: str | None = None


async def create_test_user(save_model_fixture: SaveModel, username: str, password: str) -> User:
    hashed_password = security.get_password_hash(password)
    user = User(username=username, hashed_password=hashed_password)
    await save_model_fixture(user)
    return user


@pytest_asyncio.fixture
async def auth_as(
    request: pytest.FixtureRequest, save_model_fixture: SaveModel
) -> User | Anonymous | None:
    authenticate_as: AuthenticateAs = request.param

    if authenticate_as.type_ == "dont_override":
        return None

    if authenticate_as.type_ == "anonymous":
        return Anonymous()

    uuid_ = str(uuid.uuid4())
    username = authenticate_as.username or "user" + "/" + uuid_
    hashed_password = get_password_hash(authenticate_as.password or uuid_)

    user = User(username=username, hashed_password=hashed_password)
    await save_model_fixture(user)
    return user


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "auth_as" in metafunc.fixturenames:
        pytest_params = []

        auth_marker = metafunc.definition.get_closest_marker("auth")

        if auth_marker is not None:
            args: tuple[Any] = auth_marker.args
            if len(args) == 0:
                args = (AuthenticateAs(type_="anonymous"),)

            for arg in args:
                if not isinstance(arg, AuthenticateAs):
                    raise ValueError(
                        f"auth marker arguments must be of type 'AuthenticateAs', got {type(arg)}"
                    )
                pytest_params.append(pytest.param(arg, id=repr(arg)))  # type: ignore
        else:
            pytest_params = [pytest.param(AuthenticateAs(type_="anonymous"))]

        metafunc.parametrize("auth_as", pytest_params, indirect=["auth_as"])
