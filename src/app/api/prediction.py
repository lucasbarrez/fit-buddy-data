"""Machine prediction endpoint.

Provides machine availability prediction based on sensor data
and historical usage patterns.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.models import PredictionResponse, PredictionData, ErrorResponse, RequestType
from src.algorithm import (
    predict_machine_availability_present,
    predict_machine_availability_future,
    get_all_machines,
    load_simulated_db,
)

router = APIRouter(prefix="/machine", tags=["Machine Prediction"])


VALID_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def validate_time_format(time: str) -> bool:
    """Validate time format is HH:MM."""
    try:
        parts = time.split(":")
        if len(parts) != 2:
            return False
        hour, minute = int(parts[0]), int(parts[1])
        return 0 <= hour <= 23 and 0 <= minute <= 59
    except (ValueError, AttributeError):
        return False


def is_datetime_in_past(day: str, time: str) -> bool:
    """Check if the specified day/time is in the past.
    
    For simplicity, we consider it past if:
    - The day is before today in the current week, OR
    - The day is today and the time has passed
    """
    now = datetime.now()
    current_day = now.strftime("%A").lower()
    current_time = now.strftime("%H:%M")
    
    day_order = {d: i for i, d in enumerate(VALID_DAYS)}
    
    target_day_idx = day_order.get(day.lower())
    current_day_idx = day_order.get(current_day)
    
    if target_day_idx is None or current_day_idx is None:
        return False  # Invalid day handled elsewhere
    
    # If target day is earlier in the week
    if target_day_idx < current_day_idx:
        return True
    
    # If same day, check time
    if target_day_idx == current_day_idx:
        return time < current_time
    
    return False


@router.get(
    "/{machine_id}/prediction",
    response_model=PredictionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        404: {"model": ErrorResponse, "description": "Machine not found"},
    },
    summary="Predict machine availability",
    description="""
Predict if a machine will be available at a specified time.

**Behavior:**
- **No day/time specified**: Returns current machine status (occupied or free) 
  and estimated wait time if occupied.
- **Future day/time specified**: Returns prediction based on historical usage patterns.
- **Past day/time specified**: Returns error.

**Examples:**
- Current status: `GET /machine/DC_BENCH_001/prediction`
- Future prediction: `GET /machine/DC_BENCH_001/prediction?day=thursday&time=14:00`
    """,
)
async def get_machine_prediction(
    machine_id: str,
    day: Optional[str] = Query(
        default=None,
        description="Day of the week (monday, tuesday, ..., sunday). Required with 'time'.",
        examples=["thursday", "monday"],
    ),
    time: Optional[str] = Query(
        default=None,
        description="Time in HH:MM format. Required with 'day'.",
        examples=["14:00", "09:30"],
    ),
) -> PredictionResponse:
    """
    Get machine availability prediction.
    
    Args:
        machine_id: Machine identifier (e.g., DC_BENCH_001)
        day: Optional day of the week for future prediction
        time: Optional time in HH:MM format for future prediction
        
    Returns:
        PredictionResponse with availability status and wait time
        
    Raises:
        HTTPException 400: Invalid parameters or past datetime
        HTTPException 404: Machine not found
    """
    # Validate that day and time are both provided or both absent
    if (day is None) != (time is None):
        raise HTTPException(
            status_code=400,
            detail={
                "status": False,
                "error": "Invalid parameters",
                "detail": "Both 'day' and 'time' must be provided together, or neither.",
            },
        )
    
    # Validate day format
    if day is not None and day.lower() not in VALID_DAYS:
        raise HTTPException(
            status_code=400,
            detail={
                "status": False,
                "error": "Invalid day",
                "detail": f"Day must be one of: {', '.join(VALID_DAYS)}",
            },
        )
    
    # Validate time format
    if time is not None and not validate_time_format(time):
        raise HTTPException(
            status_code=400,
            detail={
                "status": False,
                "error": "Invalid time format",
                "detail": "Time must be in HH:MM format (e.g., 14:00)",
            },
        )
    
    # Check for past datetime
    if day is not None and time is not None:
        if is_datetime_in_past(day, time):
            raise HTTPException(
                status_code=400,
                detail={
                    "status": False,
                    "error": "Invalid datetime",
                    "detail": "Cannot query past datetime. Please provide a future datetime or omit for current state.",
                },
            )
    
    try:
        # PRESENT: No datetime specified
        if day is None and time is None:
            available, time_to_wait, message = predict_machine_availability_present(
                machine_id
            )
            return PredictionResponse(
                status=True,
                data=PredictionData(available=available, time_to_wait=time_to_wait),
                request_type=RequestType.PRESENT,
                message=message,
            )
        
        # FUTURE: Datetime specified
        # At this point, day and time are guaranteed to be not None (validated above)
        assert day is not None and time is not None
        available, time_to_wait, message = predict_machine_availability_future(
            machine_id, day.lower(), time
        )
        return PredictionResponse(
            status=True,
            data=PredictionData(available=available, time_to_wait=time_to_wait),
            request_type=RequestType.FUTURE,
            message=message,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "status": False,
                "error": "Machine not found",
                "detail": str(e),
            },
        )


@router.get(
    "/list",
    summary="List all available machines",
    description="Returns a list of all machine IDs in the system.",
)
async def list_machines() -> dict:
    """Get list of all available machine IDs."""
    db = load_simulated_db()
    machines = get_all_machines(db)
    return {
        "status": True,
        "machines": machines,
        "count": len(machines),
    }
