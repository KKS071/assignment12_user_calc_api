# tests/integration/test_calculation_schema.py

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.calculation import (
    CalculationCreate,
    CalculationResponse,
    CalculationUpdate,
)


def test_create_valid():
    calc = CalculationCreate(type="addition", inputs=[10.5, 3.0], user_id=uuid4())
    assert calc.type == "addition"
    assert calc.inputs == [10.5, 3.0]


def test_create_missing_type():
    with pytest.raises(ValidationError) as exc:
        CalculationCreate(inputs=[10.5, 3.0], user_id=uuid4())
    assert "required" in str(exc.value).lower()


def test_create_missing_inputs():
    with pytest.raises(ValidationError) as exc:
        CalculationCreate(type="multiplication", user_id=uuid4())
    assert "required" in str(exc.value).lower()


def test_create_invalid_inputs_not_list():
    with pytest.raises(ValidationError) as exc:
        CalculationCreate(type="division", inputs="not-a-list", user_id=uuid4())
    assert "input should be a valid list" in str(exc.value).lower()


def test_create_unsupported_type():
    with pytest.raises(ValidationError) as exc:
        CalculationCreate(type="square_root", inputs=[25, 1], user_id=uuid4())
    err = str(exc.value).lower()
    assert "one of" in err or "not a valid" in err


def test_create_too_few_inputs():
    with pytest.raises(ValidationError):
        CalculationCreate(type="addition", inputs=[5.0], user_id=uuid4())


def test_create_division_by_zero():
    with pytest.raises(ValidationError):
        CalculationCreate(type="division", inputs=[100, 0], user_id=uuid4())


def test_update_valid():
    upd = CalculationUpdate(inputs=[42.0, 7.0])
    assert upd.inputs == [42.0, 7.0]


def test_update_no_fields():
    upd = CalculationUpdate()
    assert upd.inputs is None


def test_update_too_few_inputs():
    with pytest.raises(ValidationError):
        CalculationUpdate(inputs=[1.0])


def test_response_valid():
    data = {
        "id": uuid4(),
        "user_id": uuid4(),
        "type": "subtraction",
        "inputs": [20, 5],
        "result": 15.0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    resp = CalculationResponse(**data)
    assert resp.type == "subtraction"
    assert resp.result == 15.0
