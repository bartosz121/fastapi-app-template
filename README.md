# FastAPI REST API Template

- **Python 3.13**
- **uv**
- **Pyright**
- [**Poe**](https://github.com/nat-n/poethepoet) task runner
- **Database Setup** (SQLite by default)
- **Alembic Migrations**
- [**CLI Tool**](/todo_api/cli/__main__.py)
  - `uv run poe cli -h`
  - `add_package` command: bootstraps a new Python package with CRUD operations and tests. See source for details
- [**Generic SQLAlchemy async service**](todo_api/core/service/sqlalchemy.py)
- **Session-based Authentication:** Integrated with FastAPI dependency injection system
- **User Management**
- **Tests setup:** Includes database session management and authentication fixtures
- **Github Actions** runs `lint`, `typecheck` tasks and tests

**Note on Timezone Handling:**

If switching from SQLite to another database (e.g., PostgreSQL), review `todo_api/auth/dependencies.py`. A `TODO:` comment indicates a SQLite-specific timezone conversion that may need removal or adjustment

## Renaming the Project

To rename the project from `todo_api` to a custom name, use the included script.

**Usage:**

```bash
./rename_project.sh <new-project-name>
```

The script will rename the directory, update imports, and modify `pyproject.toml`. It is intended for one-time use.

**Seed data for tests:**

Use `seed_db` fixture in `tests/fixtures/database.py` to add seed data for your tests
