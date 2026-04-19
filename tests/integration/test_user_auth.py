# tests/integration/test_user_auth.py

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User


def test_password_hashing(db_session, fake_user_data):
    """Hash and verify a password round-trip."""
    plain = "TestPass123"
    hashed = User.hash_password(plain)
    user = User(
        first_name=fake_user_data["first_name"],
        last_name=fake_user_data["last_name"],
        email=fake_user_data["email"],
        username=fake_user_data["username"],
        password=hashed,
    )
    assert user.verify_password(plain) is True
    assert user.verify_password("WrongPass123") is False
    assert hashed != plain


def test_user_registration(db_session, fake_user_data):
    """User.register creates a correctly-configured user."""
    fake_user_data["password"] = "TestPass123"
    user = User.register(db_session, fake_user_data)
    db_session.commit()

    assert user.first_name == fake_user_data["first_name"]
    assert user.email == fake_user_data["email"]
    assert user.is_active is True
    assert user.is_verified is False
    assert user.verify_password("TestPass123") is True


def test_duplicate_registration_raises(db_session):
    """Re-registering with the same email raises ValueError."""
    data1 = {
        "first_name": "Test", "last_name": "One",
        "email": "dup@example.com", "username": "dupuser1", "password": "TestPass123",
    }
    data2 = {
        "first_name": "Test", "last_name": "Two",
        "email": "dup@example.com", "username": "dupuser2", "password": "TestPass123",
    }
    User.register(db_session, data1)
    db_session.commit()

    with pytest.raises(ValueError, match="Username or email already exists"):
        User.register(db_session, data2)


def test_authentication_success(db_session, fake_user_data):
    """Authenticate returns a dict with tokens on correct credentials."""
    fake_user_data["password"] = "TestPass123"
    User.register(db_session, fake_user_data)
    db_session.commit()

    result = User.authenticate(db_session, fake_user_data["username"], "TestPass123")
    assert result is not None
    assert "access_token" in result
    assert "refresh_token" in result
    assert result["token_type"] == "bearer"
    assert "user" in result


def test_authentication_failure(db_session, fake_user_data):
    """Authenticate returns None on wrong password."""
    fake_user_data["password"] = "TestPass123"
    User.register(db_session, fake_user_data)
    db_session.commit()

    result = User.authenticate(db_session, fake_user_data["username"], "WrongPass!")
    assert result is None


def test_last_login_updated(db_session, fake_user_data):
    """last_login is None before auth and set after a successful auth."""
    fake_user_data["password"] = "TestPass123"
    user = User.register(db_session, fake_user_data)
    db_session.commit()

    assert user.last_login is None
    User.authenticate(db_session, fake_user_data["username"], "TestPass123")
    db_session.refresh(user)
    assert user.last_login is not None


def test_unique_email_constraint(db_session):
    """Duplicate email raises ValueError via register."""
    base = {
        "first_name": "A", "last_name": "B",
        "email": "unique_c@example.com", "username": "uniqueabc",
        "password": "TestPass123",
    }
    User.register(db_session, base)
    db_session.commit()

    dup = dict(base, username="different_user")
    with pytest.raises(ValueError, match="Username or email already exists"):
        User.register(db_session, dup)


def test_short_password_rejected(db_session):
    """Passwords shorter than 6 chars raise ValueError."""
    with pytest.raises(ValueError, match="Password must be at least 6 characters long"):
        User.register(db_session, {
            "first_name": "P", "last_name": "T",
            "email": "short@example.com", "username": "shortpw",
            "password": "Ab1",
        })


def test_missing_password_rejected(db_session):
    """Missing password key raises ValueError."""
    with pytest.raises(ValueError, match="Password must be at least 6 characters long"):
        User.register(db_session, {
            "first_name": "P", "last_name": "T",
            "email": "nopw@example.com", "username": "nopwuser",
        })


def test_invalid_token_returns_none():
    """verify_token returns None for garbage tokens."""
    assert User.verify_token("not.a.valid.token") is None


def test_token_create_and_verify(db_session, fake_user_data):
    """Tokens created by create_access_token can be verified."""
    fake_user_data["password"] = "TestPass123"
    user = User.register(db_session, fake_user_data)
    db_session.commit()

    token = User.create_access_token({"sub": str(user.id)})
    decoded_id = User.verify_token(token)
    assert decoded_id == user.id


def test_authenticate_with_email(db_session, fake_user_data):
    """Users can authenticate using their email address."""
    fake_user_data["password"] = "TestPass123"
    User.register(db_session, fake_user_data)
    db_session.commit()

    result = User.authenticate(db_session, fake_user_data["email"], "TestPass123")
    assert result is not None
    assert "access_token" in result


def test_user_str_repr(test_user):
    """__str__ returns the expected format."""
    expected = f"<User(name={test_user.first_name} {test_user.last_name}, email={test_user.email})>"
    assert str(test_user) == expected


def test_user_update_method(test_user):
    """update() changes attributes and bumps updated_at."""
    original_time = test_user.updated_at
    test_user.update(first_name="Updated")
    assert test_user.first_name == "Updated"
    assert test_user.updated_at >= original_time


def test_hashed_password_property(test_user):
    """hashed_password property returns the stored password hash."""
    assert test_user.hashed_password == test_user.password
