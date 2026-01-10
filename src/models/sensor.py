from pydantic import BaseModel, Field
from typing import Optional, Dict

class SensorMetrics(BaseModel):
    """Core metrics captured by the machine sensor."""
    """Core metrics captured by the machine sensor (Source: Simulated DB)."""
    total_reps: int = Field(..., description="Total repetitions in the set")
    total_time_under_tension: float = Field(..., description="Total time under tension in seconds")
    avg_difficulty_level: float = Field(..., description="Average difficulty level (1-5)")
    
    # Velocity & Amplitude
    speed_concentric_mean: float = Field(..., description="Mean concentric speed")
    speed_concentric_max: float = Field(..., description="Max concentric speed")
    amplitude_mean: float = Field(..., description="Mean amplitude")
    amplitude_variability: float = Field(..., description="Amplitude variability (consistency metric)")

class SensorData(BaseModel):
    source: str = Field(..., description="Sensor Source ID")
    metrics: SensorMetrics
    status: str = "synced"

class SensorResponse(BaseModel):
    """Response model for sensor retrieval."""
    status: bool = True
    data: SensorData
