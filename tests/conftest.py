# tests/conftest.py

import logging
import socket
import subprocess
import time
from contextlib import contextmanager
from typing import Dict, Generator, List

import pytest
import requests
from faker import Faker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import Base, get_engine, get_sessionmaker
from app.database_init import drop_db, init_db
from app.models.user import User

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Faker setup
# ---------------------------------------------------------------------------
fake = Faker()
Faker.seed(12345)

test_engine = get_engine(database_url=settings.DATABASE_URL)
TestingSessionLocal = get_sessionmaker(engine=test_engine)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_fake_user() -> Dict[str, str]:
    """Return a dict of unique fake user data."""
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.unique.email(),
        "username": fake.unique.user_name(),
        "password": fake.password(length=12),
    }


@contextmanager
def managed_db_session():
    """Context manager for a one-off database session with rollback on error."""
    session = TestingSessionLocal()
    try:
        yield session
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def setup_test_database(request):
    """Create tables before the session and drop them after (unless --preserve-db)."""
    logger.info("Setting up test database…")
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    init_db()
    logger.info("Test database ready.")
    yield
    if not request.config.getoption("--preserve-db"):
        logger.info("Dropping test database tables…")
        drop_db()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Test-scoped database session with auto-commit/rollback."""
    session = TestingSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Test-data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_user_data() -> Dict[str, str]:
    return create_fake_user()


@pytest.fixture
def test_user(db_session: Session) -> User:
    user_data = create_fake_user()
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def seed_users(db_session: Session, request) -> List[User]:
    count = getattr(request, "param", 5)
    users = [User(**create_fake_user()) for _ in range(count)]
    db_session.add_all(users)
    db_session.commit()
    return users


# ---------------------------------------------------------------------------
# FastAPI server fixture (integration / e2e tests)
# ---------------------------------------------------------------------------

class ServerStartupError(Exception):
    pass


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _wait_for_server(url: str, timeout: int = 30) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if requests.get(url).status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    return False


@pytest.fixture(scope="session")
def fastapi_server():
    """Start a live FastAPI server for end-to-end tests."""
    port = 8000
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", port)) == 0:
            port = _find_free_port()

    server_url = f"http://127.0.0.1:{port}/"
    logger.info(f"Starting FastAPI server on port {port}…")

    process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if not _wait_for_server(f"{server_url}health", timeout=30):
        process.terminate()
        raise ServerStartupError(f"Server failed to start on {server_url}")

    logger.info(f"Test server running at {server_url}")
    yield server_url

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


# ---------------------------------------------------------------------------
# Playwright fixtures (optional UI tests)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def browser_context():
    """Session-scoped Playwright browser (requires playwright to be installed)."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            yield browser
            browser.close()
    except ImportError:
        pytest.skip("playwright not installed")


@pytest.fixture
def page(browser_context):
    """Per-test Playwright page."""
    context = browser_context.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
    )
    page = context.new_page()
    yield page
    page.close()
    context.close()


# ---------------------------------------------------------------------------
# CLI options
# ---------------------------------------------------------------------------

def pytest_addoption(parser):
    parser.addoption("--preserve-db", action="store_true", help="Keep test DB after tests")
    parser.addoption("--run-slow", action="store_true", help="Run slow-marked tests")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-slow"):
        skip = pytest.mark.skip(reason="use --run-slow to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip)
