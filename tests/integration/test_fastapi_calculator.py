# tests/test_fastapi_calculator.py

"""
End-to-end integration tests against a live FastAPI server.
Requires the `fastapi_server` fixture from conftest.py.
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
import requests

from app.models.calculation import Calculation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def base_url(fastapi_server: str) -> str:
    return fastapi_server.rstrip("/")


def _parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def register_and_login(base: str, user: dict) -> dict:
    """Register then log in; return the token response dict."""
    resp = requests.post(f"{base}/auth/register", json=user)
    assert resp.status_code == 201, resp.text
    resp = requests.post(f"{base}/auth/login", json={
        "username": user["username"],
        "password": user["password"],
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


def _new_user(prefix: str = "u") -> dict:
    uid = uuid4().hex[:8]
    return {
        "first_name": "Test",
        "last_name": "User",
        "email": f"{prefix}_{uid}@example.com",
        "username": f"{prefix}_{uid}",
        "password": "SecurePass123!",
        "confirm_password": "SecurePass123!",
    }


# ---------------------------------------------------------------------------
# Health & auth
# ---------------------------------------------------------------------------

def test_health(base_url):
    resp = requests.get(f"{base_url}/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_register_user(base_url):
    payload = {
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice.smith.e2e@example.com",
        "username": "alicesmith_e2e",
        "password": "SecurePass123!",
        "confirm_password": "SecurePass123!",
    }
    resp = requests.post(f"{base_url}/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    for key in ["id", "username", "email", "first_name", "last_name", "is_active", "is_verified"]:
        assert key in data
    assert data["username"] == "alicesmith_e2e"
    assert data["is_active"] is True
    assert data["is_verified"] is False


def test_register_duplicate_rejected(base_url):
    """Registering twice with the same email must return 400."""
    payload = {
        "first_name": "Bob",
        "last_name": "Dup",
        "email": "bob.dup@example.com",
        "username": "bob_dup_e2e",
        "password": "SecurePass123!",
        "confirm_password": "SecurePass123!",
    }
    requests.post(f"{base_url}/auth/register", json=payload)
    resp = requests.post(f"{base_url}/auth/register", json=payload)
    assert resp.status_code == 400


def test_login_user(base_url):
    user = _new_user("login")
    requests.post(f"{base_url}/auth/register", json=user)
    resp = requests.post(f"{base_url}/auth/login", json={
        "username": user["username"],
        "password": user["password"],
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()

    for field, ftype in {
        "access_token": str, "refresh_token": str, "token_type": str,
        "expires_at": str, "user_id": str, "username": str,
        "email": str, "first_name": str, "last_name": str,
        "is_active": bool, "is_verified": bool,
    }.items():
        assert field in data, f"Missing: {field}"
        assert isinstance(data[field], ftype), f"Wrong type for {field}"

    assert data["token_type"].lower() == "bearer"
    expires = _parse_dt(data["expires_at"])
    assert expires > datetime.now(timezone.utc)


def test_login_wrong_password(base_url):
    user = _new_user("badpw")
    requests.post(f"{base_url}/auth/register", json=user)
    resp = requests.post(f"{base_url}/auth/login", json={
        "username": user["username"],
        "password": "WrongPassword1!",
    })
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Calculation BREAD
# ---------------------------------------------------------------------------

def test_create_addition(base_url):
    token = register_and_login(base_url, _new_user("add"))["access_token"]
    resp = requests.post(
        f"{base_url}/calculations",
        json={"type": "addition", "inputs": [10.5, 3, 2]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["result"] == 15.5


def test_create_subtraction(base_url):
    token = register_and_login(base_url, _new_user("sub"))["access_token"]
    resp = requests.post(
        f"{base_url}/calculations",
        json={"type": "subtraction", "inputs": [10, 3, 2]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["result"] == 5


def test_create_multiplication(base_url):
    token = register_and_login(base_url, _new_user("mul"))["access_token"]
    resp = requests.post(
        f"{base_url}/calculations",
        json={"type": "multiplication", "inputs": [2, 3, 4]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["result"] == 24


def test_create_division(base_url):
    token = register_and_login(base_url, _new_user("div"))["access_token"]
    resp = requests.post(
        f"{base_url}/calculations",
        json={"type": "division", "inputs": [100, 2, 5]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["result"] == 10


def test_create_requires_auth(base_url):
    resp = requests.post(
        f"{base_url}/calculations",
        json={"type": "addition", "inputs": [1, 2]},
    )
    assert resp.status_code == 401


def test_full_crud_lifecycle(base_url):
    """Browse → Read → Edit → Delete a calculation."""
    token = register_and_login(base_url, _new_user("crud"))["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create
    resp = requests.post(
        f"{base_url}/calculations",
        json={"type": "multiplication", "inputs": [3, 4]},
        headers=headers,
    )
    assert resp.status_code == 201
    calc_id = resp.json()["id"]

    # Browse (list)
    resp = requests.get(f"{base_url}/calculations", headers=headers)
    assert resp.status_code == 200
    assert any(c["id"] == calc_id for c in resp.json())

    # Read (single)
    resp = requests.get(f"{base_url}/calculations/{calc_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == calc_id

    # Edit (update inputs)
    resp = requests.put(
        f"{base_url}/calculations/{calc_id}",
        json={"inputs": [5, 6]},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == 30  # 5 * 6

    # Delete
    resp = requests.delete(f"{base_url}/calculations/{calc_id}", headers=headers)
    assert resp.status_code == 204

    # Verify gone
    resp = requests.get(f"{base_url}/calculations/{calc_id}", headers=headers)
    assert resp.status_code == 404


def test_get_nonexistent_calculation(base_url):
    token = register_and_login(base_url, _new_user("noex"))["access_token"]
    resp = requests.get(
        f"{base_url}/calculations/{uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


def test_invalid_calc_id_format(base_url):
    token = register_and_login(base_url, _new_user("inv"))["access_token"]
    resp = requests.get(
        f"{base_url}/calculations/not-a-uuid",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Direct model tests (no server needed)
# ---------------------------------------------------------------------------

def test_model_addition():
    calc = Calculation.create("addition", uuid4(), [1, 2, 3])
    assert calc.get_result() == 6


def test_model_subtraction():
    calc = Calculation.create("subtraction", uuid4(), [10, 3, 2])
    assert calc.get_result() == 5


def test_model_multiplication():
    calc = Calculation.create("multiplication", uuid4(), [2, 3, 4])
    assert calc.get_result() == 24


def test_model_division():
    calc = Calculation.create("division", uuid4(), [100, 2, 5])
    assert calc.get_result() == 10


def test_model_division_by_zero():
    with pytest.raises(ValueError):
        Calculation.create("division", uuid4(), [100, 0]).get_result()
