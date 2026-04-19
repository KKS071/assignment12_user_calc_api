# app/operations/__init__.py

from typing import Union

Number = Union[int, float]


def add(a: Number, b: Number) -> Number:
    """Return the sum of a and b."""
    return a + b


def subtract(a: Number, b: Number) -> Number:
    """Return a minus b."""
    return a - b


def multiply(a: Number, b: Number) -> Number:
    """Return the product of a and b."""
    return a * b


def divide(a: Number, b: Number) -> float:
    """Return a divided by b. Raises ValueError if b is zero."""
    if b == 0:
        raise ValueError("Cannot divide by zero!")
    return a / b
