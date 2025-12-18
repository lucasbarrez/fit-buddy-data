"""Pydantic models for machine prediction API responses."""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class RequestType(str, Enum):
    """Type of prediction request."""
    PRESENT = "present"  # No datetime specified, checking current state
    FUTURE = "future"    # Datetime in future, predicting availability


class PredictionData(BaseModel):
    """Prediction result data."""
    available: bool = Field(
        ..., 
        description="Whether the machine is available (True) or occupied (False)"
    )
    time_to_wait: int = Field(
        ..., 
        ge=0,
        description="Estimated minutes to wait before machine becomes available. 0 if already available."
    )
    

class PredictionResponse(BaseModel):
    """Response model for machine prediction endpoint."""
    status: bool = Field(
        ..., 
        description="True if the request was processed successfully"
    )
    data: PredictionData = Field(
        ..., 
        description="Prediction result data"
    )
    request_type: RequestType = Field(
        ..., 
        description="Type of request: 'present' (current state) or 'future' (prediction)"
    )
    message: Optional[str] = Field(
        default=None, 
        description="Optional message with additional context"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": True,
                    "data": {
                        "available": False,
                        "time_to_wait": 5
                    },
                    "request_type": "present",
                    "message": "Machine currently in use, estimated 5 minutes remaining"
                },
                {
                    "status": True,
                    "data": {
                        "available": True,
                        "time_to_wait": 0
                    },
                    "request_type": "future",
                    "message": "Machine predicted to be available at requested time"
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Error response model."""
    status: bool = Field(default=False, description="Always False for errors")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": False,
                    "error": "Invalid datetime",
                    "detail": "Cannot query past datetime. Please provide a future datetime or omit for current state."
                }
            ]
        }
    }
