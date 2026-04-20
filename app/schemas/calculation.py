# app/schemas/calculation.py

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CalculationType(str, Enum):
    ADDITION = "addition"
    SUBTRACTION = "subtraction"
    MULTIPLICATION = "multiplication"
    DIVISION = "division"


class CalculationBase(BaseModel):
    type: CalculationType = Field(..., example="addition")
    inputs: List[float] = Field(..., example=[10.5, 3, 2], min_length=2)

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v):
        allowed = {e.value for e in CalculationType}
        if not isinstance(v, str) or v.lower() not in allowed:
            raise ValueError(f"Type must be one of: {', '.join(sorted(allowed))}")
        return v.lower()

    @field_validator("inputs", mode="before")
    @classmethod
    def check_inputs_is_list(cls, v):
        if not isinstance(v, list):
            raise ValueError("Input should be a valid list")
        return v

    @model_validator(mode="after")
    def validate_inputs(self) -> "CalculationBase":
        if len(self.inputs) < 2:
            raise ValueError("At least two numbers are required for calculation")
        if self.type == CalculationType.DIVISION:
            if any(x == 0 for x in self.inputs[1:]):
                raise ValueError("Cannot divide by zero")
        return self

    model_config = ConfigDict(from_attributes=True)


class CalculationCreate(CalculationBase):
    """Schema for creating a calculation (user_id required)."""
    user_id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174000")


class CalculationUpdate(BaseModel):
    """Schema for updating an existing calculation's type and/or inputs."""
    type: Optional[CalculationType] = Field(None, example="multiplication")
    inputs: Optional[List[float]] = Field(None, example=[42, 7], min_length=2)

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v):
        if v is None:
            return v
        allowed = {e.value for e in CalculationType}
        if not isinstance(v, str) or v.lower() not in allowed:
            raise ValueError(f"Type must be one of: {', '.join(sorted(allowed))}")
        return v.lower()

    @model_validator(mode="after")
    def validate_inputs(self) -> "CalculationUpdate":
        if self.inputs is not None and len(self.inputs) < 2:
            raise ValueError("At least two numbers are required for calculation")
        # Guard division-by-zero when switching type to division
        if self.type == CalculationType.DIVISION and self.inputs is not None:
            if any(x == 0 for x in self.inputs[1:]):
                raise ValueError("Cannot divide by zero")
        return self

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "type": "multiplication",
                "inputs": [5, 6]
            }
        }
    )


class CalculationResponse(CalculationBase):
    """Schema returned from the API for a saved calculation."""
    id: UUID
    user_id: UUID
    result: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)