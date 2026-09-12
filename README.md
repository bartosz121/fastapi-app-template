# FastAPI REST API Template

- **Python 3.14**
- **uv**
- **Pyright**
- [**Poe**](https://github.com/nat-n/poethepoet) task runner
- **Database Setup** (PostgreSQL by default)
- **Alembic Migrations**
- [**CLI Tool**](todo_api/cli/__main__.py)
  - `uv run poe cli -h`
  - `add_package` command: bootstraps a new Python package with CRUD operations and tests. See source for details
- [**Generic SQLAlchemy async service**](todo_api/core/database/service.py)
- **OpenTelemetry instrumentation:** Configurable with `OTEL_ENABLED`
- **Prometheus metrics:** Configurable with `PROMETHEUS_ENABLED`
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

Build, Start, Run tests:

```bash
docker compose -f docker/compose.yaml -f docker/compose.dev.yaml build

docker compose -f docker/compose.yaml -f docker/compose.dev.yaml up --watch

docker exec -it todo-api poe test
```
