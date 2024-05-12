import sys
from random import randint

from faker import Faker

from todo_api.core.database.base import session_factory
from todo_api.todos.models import Todo
from todo_api.users.models import User
from todo_api.users.security import get_password_hash

PASSWORD = "passw0rd123!@#"

if __name__ == "__main__":
    n_users = int(sys.argv[1])
    n_todos = int(sys.argv[2])
    fake = Faker()
    session = session_factory()

    hashed_password = get_password_hash(PASSWORD)
    for _ in range(n_users):
        user = User(
            username=fake.user_name(),
            hashed_password=hashed_password,
        )
        print(f"{user=!r}")
        session.add(user)

    for _ in range(n_todos):
        todo = Todo(
            title=fake.sentence(nb_words=12),
            description=fake.sentence(nb_words=50),
            is_completed=fake.boolean(50),
            user_id=randint(0, n_users),
        )
        print(f"{todo=!r}")
        session.add(todo)

    session.commit()
