"""
Pytest configuration and shared fixtures for the backend test suite.

Database isolation strategy
-----------------------------
Each test that touches the database runs inside a transaction that is rolled
back at teardown, so every test starts from a clean slate without the overhead
of dropping and recreating tables.

Environment variables
---------------------
TEST_DATABASE_URL  – preferred connection string for tests
DATABASE_URL       – fallback used by the production app
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Make sure the backend package root is importable when pytest is run from
# either the repo root or the backend/ directory.
# ---------------------------------------------------------------------------
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)


# ---------------------------------------------------------------------------
# Point the database layer at the test database *before* importing app/services
# ---------------------------------------------------------------------------
_test_db_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
if _test_db_url:
    os.environ["DATABASE_URL"] = _test_db_url


# ---------------------------------------------------------------------------
# App & service imports (deferred so the env-var patch above takes effect first)
# ---------------------------------------------------------------------------
from app import app  # noqa: E402  (import after env setup)
from services.database import connection  # noqa: E402
from services.auth_service import hash_password, create_token  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _truncate_all(db) -> None:
    """Remove all test data from every user-facing table."""
    # Order matters: child rows before parent rows.
    db.execute("DELETE FROM face_embeddings")
    db.execute("DELETE FROM gallery_photos")
    db.execute("DELETE FROM users")


def _insert_user(db, email: str, full_name: str, password: str = "TestPass123!") -> dict:
    """Insert a user with a hashed password and return their row as a dict."""
    row = db.execute(
        "INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?) RETURNING *",
        (email.lower(), hash_password(password), full_name),
    ).fetchone()
    return dict(row)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def client() -> TestClient:
    """A single TestClient instance shared across the whole test session."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# Alias used by some tasks that import `test_client` by that exact name.
@pytest.fixture(scope="session")
def test_client(client: TestClient) -> TestClient:
    return client


@pytest.fixture(autouse=True)
def clean_db():
    """
    Truncate all tables before each test so every test starts from a clean
    state regardless of execution order.

    Truncation (rather than transaction rollback) is used because psycopg's
    autocommit behaviour inside TestClient makes open-transaction isolation
    unreliable across HTTP calls.
    """
    with connection() as db:
        _truncate_all(db)
    yield
    # Post-test cleanup is optional but keeps the DB tidy during interactive
    # debugging sessions.
    with connection() as db:
        _truncate_all(db)


@pytest.fixture()
def test_user() -> dict:
    """
    Insert a primary test user and return their dict (including ``id``).
    The ``clean_db`` fixture guarantees this user is the only one present.
    """
    with connection() as db:
        user = _insert_user(db, "testuser@example.com", "Test User")
    return user


@pytest.fixture()
def test_user_b() -> dict:
    """
    Insert a second test user for ownership-isolation tests.
    Both ``test_user`` and ``test_user_b`` can be requested in the same test.
    """
    with connection() as db:
        user = _insert_user(db, "testuser_b@example.com", "Test User B")
    return user


@pytest.fixture()
def auth_headers(test_user: dict) -> dict:
    """
    Return ``Authorization: Bearer <token>`` headers for the primary test user.
    """
    token = create_token(test_user["id"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth_headers_b(test_user_b: dict) -> dict:
    """
    Return ``Authorization: Bearer <token>`` headers for the secondary test user.
    """
    token = create_token(test_user_b["id"])
    return {"Authorization": f"Bearer {token}"}
