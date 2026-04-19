# tests/integration/test_calculation.py

import uuid
import pytest

from app.models.calculation import (
    Addition,
    Calculation,
    Division,
    Multiplication,
    Subtraction,
)


def dummy_uid():
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# get_result tests
# ---------------------------------------------------------------------------

def test_addition_result():
    inputs = [10, 5, 3.5]
    calc = Addition(user_id=dummy_uid(), inputs=inputs)
    assert calc.get_result() == sum(inputs)


def test_subtraction_result():
    calc = Subtraction(user_id=dummy_uid(), inputs=[20, 5, 3])
    assert calc.get_result() == 12  # 20 - 5 - 3


def test_multiplication_result():
    calc = Multiplication(user_id=dummy_uid(), inputs=[2, 3, 4])
    assert calc.get_result() == 24


def test_division_result():
    calc = Division(user_id=dummy_uid(), inputs=[100, 2, 5])
    assert calc.get_result() == 10  # 100 / 2 / 5


def test_division_by_zero():
    calc = Division(user_id=dummy_uid(), inputs=[50, 0, 5])
    with pytest.raises(ValueError, match="Cannot divide by zero."):
        calc.get_result()


# ---------------------------------------------------------------------------
# Factory method tests
# ---------------------------------------------------------------------------

def test_factory_addition():
    calc = Calculation.create("addition", dummy_uid(), [1, 2, 3])
    assert isinstance(calc, Addition)
    assert calc.get_result() == 6


def test_factory_subtraction():
    calc = Calculation.create("subtraction", dummy_uid(), [10, 4])
    assert isinstance(calc, Subtraction)
    assert calc.get_result() == 6


def test_factory_multiplication():
    calc = Calculation.create("multiplication", dummy_uid(), [3, 4, 2])
    assert isinstance(calc, Multiplication)
    assert calc.get_result() == 24


def test_factory_division():
    calc = Calculation.create("division", dummy_uid(), [100, 2, 5])
    assert isinstance(calc, Division)
    assert calc.get_result() == 10


def test_factory_invalid_type():
    with pytest.raises(ValueError, match="Unsupported calculation type"):
        Calculation.create("modulus", dummy_uid(), [10, 3])


# ---------------------------------------------------------------------------
# Input validation edge cases
# ---------------------------------------------------------------------------

def test_addition_non_list_inputs():
    calc = Addition(user_id=dummy_uid(), inputs="not-a-list")
    with pytest.raises(ValueError, match="Inputs must be a list of numbers."):
        calc.get_result()


def test_subtraction_too_few_inputs():
    calc = Subtraction(user_id=dummy_uid(), inputs=[10])
    with pytest.raises(ValueError, match="Inputs must be a list with at least two numbers."):
        calc.get_result()


def test_division_too_few_inputs():
    calc = Division(user_id=dummy_uid(), inputs=[10])
    with pytest.raises(ValueError, match="Inputs must be a list with at least two numbers."):
        calc.get_result()


def test_repr():
    calc = Addition(user_id=dummy_uid(), inputs=[1, 2])
    assert "Calculation" in repr(calc)
