# tests/integration/test_user.py

import logging

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from tests.conftest import create_fake_user, managed_db_session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Connection & session tests
# ---------------------------------------------------------------------------

def test_database_connection(db_session):
    result = db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


def test_managed_session_context_manager():
    """managed_db_session handles errors and triggers rollback."""
    with managed_db_session() as session:
        session.execute(text("SELECT 1"))
        try:
            session.execute(text("SELECT * FROM nonexistent_table"))
        except Exception as e:
            assert "nonexistent_table" in str(e)


# ---------------------------------------------------------------------------
# Session / partial-commit tests
# ---------------------------------------------------------------------------

def test_session_handling(db_session):
    """
    user1 commits, user2 fails on duplicate email (rollback), user3 commits.
    Net result: initial + 2 users.
    """
    initial = db_session.query(User).count()

    user1 = User(first_name="U", last_name="One", email="u1_sh@example.com",
                 username="u1_sh", password="hashed")
    db_session.add(user1)
    db_session.commit()

    # Duplicate email → should fail
    user2 = User(first_name="U", last_name="Two", email="u1_sh@example.com",
                 username="u2_sh", password="hashed")
    db_session.add(user2)
    try:
        db_session.commit()
    except Exception:
        db_session.rollback()

    user3 = User(first_name="U", last_name="Three", email="u3_sh@example.com",
                 username="u3_sh", password="hashed")
    db_session.add(user3)
    db_session.commit()

    assert db_session.query(User).count() == initial + 2


# ---------------------------------------------------------------------------
# Creation tests
# ---------------------------------------------------------------------------

def test_create_user_with_faker(db_session):
    data = create_fake_user()
    user = User(**data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == data["email"]


def test_create_multiple_users(db_session):
    users = [User(**create_fake_user()) for _ in range(3)]
    db_session.add_all(users)
    db_session.commit()
    assert len(users) == 3


# ---------------------------------------------------------------------------
# Query tests
# ---------------------------------------------------------------------------

def test_query_methods(db_session, seed_users):
    count = db_session.query(User).count()
    assert count >= len(seed_users)

    found = db_session.query(User).filter_by(email=seed_users[0].email).first()
    assert found is not None

    ordered = db_session.query(User).order_by(User.email).all()
    assert len(ordered) >= len(seed_users)


# ---------------------------------------------------------------------------
# Transaction rollback tests
# ---------------------------------------------------------------------------

def test_transaction_rollback(db_session):
    initial = db_session.query(User).count()
    try:
        data = create_fake_user()
        db_session.add(User(**data))
        db_session.execute(text("SELECT * FROM nonexistent_table"))
        db_session.commit()
    except Exception:
        db_session.rollback()

    assert db_session.query(User).count() == initial


# ---------------------------------------------------------------------------
# Update tests
# ---------------------------------------------------------------------------

def test_update_with_refresh(db_session, test_user):
    original_time = test_user.updated_at
    new_email = f"updated_{test_user.email}"
    test_user.email = new_email
    db_session.commit()
    db_session.refresh(test_user)

    assert test_user.email == new_email
    assert test_user.updated_at >= original_time


# ---------------------------------------------------------------------------
# Bulk operation (slow)
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_bulk_operations(db_session):
    users = [User(**create_fake_user()) for _ in range(10)]
    db_session.bulk_save_objects(users)
    db_session.commit()
    assert db_session.query(User).count() >= 10


# ---------------------------------------------------------------------------
# Uniqueness constraint tests
# ---------------------------------------------------------------------------

def test_unique_email_constraint(db_session):
    data = create_fake_user()
    db_session.add(User(**data))
    db_session.commit()

    dup = create_fake_user()
    dup["email"] = data["email"]
    db_session.add(User(**dup))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_unique_username_constraint(db_session):
    data = create_fake_user()
    db_session.add(User(**data))
    db_session.commit()

    dup = create_fake_user()
    dup["username"] = data["username"]
    db_session.add(User(**dup))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_persistence_after_constraint_violation(db_session):
    """The original valid user survives after a duplicate attempt."""
    valid = {
        "first_name": "Good", "last_name": "User",
        "email": "persist_test@example.com", "username": "persistuser",
        "password": "pw123",
    }
    original = User(**valid)
    db_session.add(original)
    db_session.commit()
    saved_id = original.id

    try:
        db_session.add(User(
            first_name="Bad", last_name="Dup",
            email="persist_test@example.com",  # duplicate
            username="otheruser", password="pw456",
        ))
        db_session.commit()
        assert False, "Expected IntegrityError"
    except IntegrityError:
        db_session.rollback()

    found = db_session.query(User).filter_by(id=saved_id).first()
    assert found is not None
    assert found.email == "persist_test@example.com"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_error_handling():
    with pytest.raises(Exception) as exc:
        with managed_db_session() as session:
            session.execute(text("INVALID SQL"))
    assert "INVALID SQL" in str(exc.value)
