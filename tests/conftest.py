"""
PostgreSQL test databases are created from a template.

Each xdist worker gets its own schema-only template database. Every DB-backed
test then gets a fresh cloned database created from that template and dropped
after the test finishes.

Tests that do not use the DB fixture chain do not trigger any PostgreSQL setup.
"""

import hashlib
import os
import re


def _sanitize_identifier(value: str) -> str:
    """Normalize a string into a Postgres-friendly identifier fragment."""
    sanitized_value = re.sub(r"[^a-zA-Z0-9_]", "_", value).strip("_").lower()
    return sanitized_value or "test"


def _truncate_identifier(identifier: str, *, hash_source: str) -> str:
    """Trim long identifiers to PostgreSQL's limit while preserving uniqueness."""
    if len(identifier) <= 63:
        return identifier

    suffix = hashlib.sha1(hash_source.encode("utf-8")).hexdigest()[:12]
    prefix_length = 63 - len(suffix) - 1
    return f"{identifier[:prefix_length]}_{suffix}"


def _build_template_database_name(base_name: str) -> str:
    """Build a template database name unique to the current xdist worker."""
    test_run_uid = os.environ.get("PYTEST_XDIST_TESTRUNUID", f"local_{os.getpid()}")
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
    database_name = "_".join(
        (
            _sanitize_identifier(base_name),
            "template",
            _sanitize_identifier(test_run_uid),
            _sanitize_identifier(worker_id),
        )
    )
    return _truncate_identifier(database_name, hash_source=database_name)


BASE_TEST_DATABASE = os.environ.get("DB_DATABASE", "todo_api_test")
os.environ["ENVIRONMENT"] = "TESTING"
os.environ["DB_TEMPLATE_DATABASE"] = _build_template_database_name(BASE_TEST_DATABASE)


from tests.fixtures import *  # noqa: E402, F403
