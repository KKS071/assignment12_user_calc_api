# tests/integration/test_schema_base.py

import pytest
from pydantic import ValidationError

from app.schemas.base import PasswordMixin, UserBase, UserCreate, UserLogin


def test_user_base_valid():
    u = UserBase(first_name="John", last_name="Doe", email="john@example.com", username="johndoe")
    assert u.first_name == "John"
    assert u.email == "john@example.com"


def test_user_base_invalid_email():
    with pytest.raises(ValidationError):
        UserBase(first_name="John", last_name="Doe", email="not-an-email", username="johndoe")


def test_password_mixin_valid():
    p = PasswordMixin(password="SecurePass123")
    assert p.password == "SecurePass123"


def test_password_mixin_too_short():
    with pytest.raises(ValidationError):
        PasswordMixin(password="Short1")


def test_password_mixin_no_uppercase():
    with pytest.raises(ValidationError, match="uppercase"):
        PasswordMixin(password="lowercase123")


def test_password_mixin_no_lowercase():
    with pytest.raises(ValidationError, match="lowercase"):
        PasswordMixin(password="UPPERCASE123")


def test_password_mixin_no_digit():
    with pytest.raises(ValidationError, match="digit"):
        PasswordMixin(password="NoDigitsHere")


def test_user_create_valid():
    u = UserCreate(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        username="johndoe",
        password="SecurePass123",
    )
    assert u.username == "johndoe"


def test_user_create_invalid_password():
    with pytest.raises(ValidationError):
        UserCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            username="johndoe",
            password="short",
        )


def test_user_login_valid():
    login = UserLogin(username="johndoe", password="SecurePass123")
    assert login.username == "johndoe"


def test_user_login_username_too_short():
    with pytest.raises(ValidationError):
        UserLogin(username="jd", password="SecurePass123")


def test_user_login_password_too_short():
    with pytest.raises(ValidationError):
        UserLogin(username="johndoe", password="short")
