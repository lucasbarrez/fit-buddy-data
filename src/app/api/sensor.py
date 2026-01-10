from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from src.models.sensor import SensorResponse, SensorData, SensorMetrics
from src.models.prediction import ErrorResponse
from src.services.sensor import SensorService

router = APIRouter(prefix="/sensor", tags=["Sensor Data"])

@router.get(
    "/metrics",
    response_model=SensorResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid parameters"},
        404: {"model": ErrorResponse, "description": "Machine or Sensor not found"},
    },
    summary="Get sensor metrics from simulated DB",
)
async def get_sensor_metrics(
    machine_id: str = Query(..., description="Machine Identifier"),
    start_time: str = Query(..., description="Start timestamp (ISO 8601)"),
    end_time: str = Query(..., description="End timestamp (ISO 8601)")
) -> SensorResponse:
    """
    Retrieve sensor data for a completed set from the JSON database.
    
    It looks up the machine's sensor and returns a sample set summary
    from 'set_summary' to provide realistic data.
    """
    
    # 1. Basic Validation
    try:
        dt_start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        dt_end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"status": False, "error": "Invalid timestamp format", "detail": "Use ISO 8601"}
        )

    if dt_end <= dt_start:
            raise HTTPException(
            status_code=400,
            detail={"status": False, "error": "Invalid duration", "detail": "End time must be after start time"}
        )

    # 2. Delegate to Service
    try:
        metrics = SensorService.get_metrics_for_period(machine_id, dt_start, dt_end)
    except ValueError as e:
         raise HTTPException(
            status_code=404,
            detail={"status": False, "error": "Machine not found", "detail": str(e)}
        )
        
    if not metrics:
         raise HTTPException(
            status_code=404,
            detail={"status": False, "error": "No Activity Found", "detail": "No sensor activity detected in this time window."}
        )

    return SensorResponse(
        status=True,
        data=SensorData(
            source=f"Sensor_{machine_id}",
            metrics=metrics,
            status="synced"
        )
    )
