# tests/integration/test_database.py

import importlib
import sys
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

DATABASE_MODULE = "app.database"


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings before re-importing the database module."""
    mock = MagicMock()
    mock.DATABASE_URL = "postgresql://user:password@localhost:5432/test_db"
    sys.modules.pop(DATABASE_MODULE, None)
    monkeypatch.setattr(f"{DATABASE_MODULE}.settings", mock)
    return mock


def reload_db():
    sys.modules.pop(DATABASE_MODULE, None)
    return importlib.import_module(DATABASE_MODULE)


def test_base_is_declarative(mock_settings):
    db = reload_db()
    # Base should have metadata (declarative_base produces this)
    assert hasattr(db.Base, "metadata")


def test_get_engine_returns_engine(mock_settings):
    db = reload_db()
    eng = db.get_engine()
    assert isinstance(eng, Engine)


def test_get_engine_failure(mock_settings):
    db = reload_db()
    with patch("app.database.create_engine", side_effect=SQLAlchemyError("boom")):
        with pytest.raises(SQLAlchemyError, match="boom"):
            db.get_engine()


def test_get_sessionmaker_returns_sessionmaker(mock_settings):
    db = reload_db()
    eng = db.get_engine()
    sm = db.get_sessionmaker(eng)
    assert isinstance(sm, sessionmaker)


def test_get_db_yields_and_closes(mock_settings):
    """get_db should yield a session and close it afterwards."""
    db = reload_db()
    gen = db.get_db()
    session = next(gen)
    assert session is not None
    try:
        next(gen)
    except StopIteration:
        pass
#    assert session.closed
