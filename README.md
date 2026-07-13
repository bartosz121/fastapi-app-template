# FastAPI REST API Template

- **Python 3.14**
- **uv**
- **Pyright**
- [**Poe**](https://github.com/nat-n/poethepoet) task runner
- **Database Setup** (SQLite by default)
- **Alembic Migrations**
- [**CLI Tool**](/todo_api/cli/__main__.py)
  - `uv run poe cli -h`
  - `add_package` command: bootstraps a new Python package with CRUD operations and tests. See source for details
- [**Generic SQLAlchemy async service**](todo_api/core/database/service.py)
- **Package boundaries:** `todo_api/core` holds database, application exceptions, logging, and observability; `todo_api/api` holds the FastAPI/REST adapter (routers, schemas, dependencies, middleware, and HTTP error handling).
- **Session-based Authentication:** Integrated with FastAPI dependency injection system
- **User Management**
- **Tests setup:** Includes database session management and authentication fixtures
- **Github Actions** runs `lint`, `typecheck` tasks and tests

**Seed data for tests:**

Use `seed_db` fixture in `tests/fixtures/database.py` to add seed data for your tests

## Renaming the Project

To rename the project from `todo_api` to a custom name, use the included script.

**Usage:**

```bash
./rename_project.sh <new-project-name>
```

The script will rename the directory, update imports, and modify `pyproject.toml`. It is intended for one-time use.
