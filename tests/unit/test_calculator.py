# tests/unit/test_calculator.py

import pytest
from typing import Union

from app.operations import add, subtract, multiply, divide

Number = Union[int, float]


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (2, 3, 5),
        (-2, -3, -5),
        (2.5, 3.5, 6.0),
        (-2.5, 3.5, 1.0),
        (0, 0, 0),
    ],
    ids=[
        "positive_ints",
        "negative_ints",
        "positive_floats",
        "mixed_floats",
        "zeros",
    ],
)
def test_add(a: Number, b: Number, expected: Number):
    assert add(a, b) == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (5, 3, 2),
        (-5, -3, -2),
        (5.5, 2.5, 3.0),
        (-5.5, -2.5, -3.0),
        (0, 0, 0),
    ],
    ids=[
        "positive_ints",
        "negative_ints",
        "positive_floats",
        "negative_floats",
        "zeros",
    ],
)
def test_subtract(a: Number, b: Number, expected: Number):
    assert subtract(a, b) == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (2, 3, 6),
        (-2, 3, -6),
        (2.5, 4.0, 10.0),
        (-2.5, 4.0, -10.0),
        (0, 5, 0),
    ],
    ids=[
        "positive_ints",
        "negative_and_positive",
        "positive_floats",
        "negative_float_and_positive",
        "zero",
    ],
)
def test_multiply(a: Number, b: Number, expected: Number):
    assert multiply(a, b) == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (6, 3, 2.0),
        (-6, 3, -2.0),
        (6.0, 3.0, 2.0),
        (-6.0, 3.0, -2.0),
        (0, 5, 0.0),
    ],
    ids=[
        "positive_ints",
        "negative_by_positive",
        "positive_floats",
        "negative_float",
        "zero_numerator",
    ],
)
def test_divide(a: Number, b: Number, expected: float):
    assert divide(a, b) == expected


def test_divide_by_zero():
    with pytest.raises(ValueError, match="Cannot divide by zero!"):
        divide(6, 0)
