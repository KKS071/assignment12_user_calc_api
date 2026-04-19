# tests/integration/test_dependencies.py

from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, status

from app.auth.dependencies import get_current_active_user, get_current_user
from app.models.user import User
from app.schemas.user import UserResponse

_now = datetime.now(timezone.utc)

sample_user = {
    "id": uuid4(),
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "is_active": True,
    "is_verified": True,
    "created_at": _now,
    "updated_at": _now,
}

inactive_user = {
    "id": uuid4(),
    "username": "inactiveuser",
    "email": "inactive@example.com",
    "first_name": "Inactive",
    "last_name": "User",
    "is_active": False,
    "is_verified": False,
    "created_at": _now,
    "updated_at": _now,
}


@pytest.fixture
def mock_verify():
    with patch.object(User, "verify_token") as m:
        yield m


def test_get_current_user_full_payload(mock_verify):
    mock_verify.return_value = sample_user
    user = get_current_user(token="tok")
    assert isinstance(user, UserResponse)
    assert user.username == "testuser"
    mock_verify.assert_called_once_with("tok")


def test_get_current_user_invalid_token(mock_verify):
    mock_verify.return_value = None
    with pytest.raises(HTTPException) as exc:
        get_current_user(token="bad")
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in exc.value.detail


def test_get_current_user_empty_dict(mock_verify):
    mock_verify.return_value = {}
    with pytest.raises(HTTPException) as exc:
        get_current_user(token="tok")
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_sub_only(mock_verify):
    mock_verify.return_value = {"sub": str(uuid4())}
    user = get_current_user(token="tok")
    assert user.username == "unknown"


def test_get_current_user_uuid(mock_verify):
    mock_verify.return_value = uuid4()
    user = get_current_user(token="tok")
    assert user.username == "unknown"


def test_get_current_active_user_active(mock_verify):
    mock_verify.return_value = sample_user
    current = get_current_user(token="tok")
    active = get_current_active_user(current_user=current)
    assert active.is_active is True


def test_get_current_active_user_inactive(mock_verify):
    mock_verify.return_value = inactive_user
    current = get_current_user(token="tok")
    with pytest.raises(HTTPException) as exc:
        get_current_active_user(current_user=current)
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.value.detail == "Inactive user"
