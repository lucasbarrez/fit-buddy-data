"""Machine availability prediction algorithm.

This module provides the core prediction logic for estimating
machine availability based on sensor data and historical patterns.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

# Path to simulated database
DATA_PATH = Path(__file__).parent.parent.parent / "data" / "simulated_db.json"

# Default estimated session duration in minutes (fallback)
DEFAULT_SESSION_DURATION = 10

# Threshold for considering a machine as "likely occupied" based on historical probability
OCCUPANCY_PROBABILITY_THRESHOLD = 0.6


def load_simulated_db() -> dict:
    """Load the simulated database from JSON file."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_sensor_for_machine(db: dict, machine_id: str) -> Optional[dict]:
    """Get the sensor associated with a machine.
    
    Args:
        db: Simulated database dict
        machine_id: Machine identifier (e.g., "DC_BENCH_001")
        
    Returns:
        Sensor dict if found, None otherwise
    """
    for sensor in db.get("sensors", []):
        if sensor["machine"] == machine_id:
            return sensor
    return None


def get_current_activity(db: dict, sensor_id: str) -> Optional[dict]:
    """Get the current ongoing activity for a sensor (end_time is null).
    
    Args:
        db: Simulated database dict
        sensor_id: UUID of the sensor
        
    Returns:
        Activity dict if machine is currently in use, None if free
    """
    for activity in db.get("sensor_activity", []):
        if activity["sensor_id"] == sensor_id and activity["end_time"] is None:
            return activity
    return None


def get_historical_set_durations(db: dict, sensor_id: str, limit: int = 10) -> list[float]:
    """Get historical session durations for a sensor.
    
    Calculates duration in minutes from completed set_summary entries.
    
    Args:
        db: Simulated database dict
        sensor_id: UUID of the sensor
        limit: Maximum number of historical records to consider
        
    Returns:
        List of session durations in minutes
    """
    durations = []
    
    for summary in db.get("set_summary", []):
        if summary["sensor_id"] == sensor_id and summary["end_time"] is not None:
            start = datetime.fromisoformat(summary["start_time"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(summary["end_time"].replace("Z", "+00:00"))
            duration_minutes = (end - start).total_seconds() / 60
            durations.append(duration_minutes)
            
            if len(durations) >= limit:
                break
    
    return durations


def calculate_average_session_duration(durations: list[float]) -> float:
    """Calculate average session duration from historical data.
    
    Args:
        durations: List of session durations in minutes
        
    Returns:
        Average duration in minutes, or DEFAULT_SESSION_DURATION if no data
    """
    if not durations:
        return DEFAULT_SESSION_DURATION
    return sum(durations) / len(durations)


def estimate_time_remaining(
    activity_start: datetime,
    average_duration: float,
    current_time: Optional[datetime] = None
) -> int:
    """Estimate remaining time for current activity.
    
    Args:
        activity_start: When the current activity started
        average_duration: Average session duration in minutes
        current_time: Current time (defaults to now if None)
        
    Returns:
        Estimated minutes remaining (minimum 1 if still in progress)
    """
    if current_time is None:
        current_time = datetime.now(activity_start.tzinfo)
    
    elapsed = (current_time - activity_start).total_seconds() / 60
    remaining = average_duration - elapsed
    
    # Return at least 1 minute if we think it's still occupied
    return max(1, int(round(remaining)))


def get_historical_occupancy_probability(
    db: dict,
    machine_id: str,
    day: str,
    time: str
) -> float:
    """Get historical occupancy probability for a specific day/time.
    
    Args:
        db: Simulated database dict
        machine_id: Machine identifier
        day: Day of week (lowercase, e.g., "thursday")
        time: Time in HH:MM format (e.g., "14:00")
        
    Returns:
        Probability between 0 and 1 (0 = likely free, 1 = likely occupied)
    """
    patterns = db.get("historical_usage_patterns", {})
    machine_patterns = patterns.get(machine_id, {})
    day_patterns = machine_patterns.get(day.lower(), {})
    
    # Try exact time match first
    if time in day_patterns:
        return day_patterns[time]
    
    # Try to find closest hour
    try:
        target_hour = int(time.split(":")[0])
        closest_time = None
        min_diff = float("inf")
        
        for t in day_patterns.keys():
            hour = int(t.split(":")[0])
            diff = abs(hour - target_hour)
            if diff < min_diff:
                min_diff = diff
                closest_time = t
        
        if closest_time:
            return day_patterns[closest_time]
    except (ValueError, IndexError):
        pass
    
    # Default to moderate probability if no data
    return 0.5


def predict_machine_availability_present(machine_id: str) -> Tuple[bool, int, str]:
    """Predict current machine availability.
    
    Checks if the machine is currently in use and estimates wait time.
    
    Args:
        machine_id: Machine identifier (e.g., "DC_BENCH_001")
        
    Returns:
        Tuple of (available: bool, time_to_wait: int, message: str)
        
    Raises:
        ValueError: If machine_id is not found
    """
    db = load_simulated_db()
    
    # Find sensor for this machine
    sensor = get_sensor_for_machine(db, machine_id)
    if sensor is None:
        raise ValueError(f"Machine '{machine_id}' not found")
    
    sensor_id = sensor["sensor_id"]
    
    # Check for current activity
    current_activity = get_current_activity(db, sensor_id)
    
    if current_activity is None:
        # Machine is free
        return True, 0, "Machine is currently available"
    
    # Machine is occupied - estimate remaining time
    activity_start = datetime.fromisoformat(
        current_activity["start_time"].replace("Z", "+00:00")
    )
    
    # Get historical durations for this sensor
    historical_durations = get_historical_set_durations(db, sensor_id)
    avg_duration = calculate_average_session_duration(historical_durations)
    
    # Estimate remaining time
    time_remaining = estimate_time_remaining(activity_start, avg_duration)
    
    message = (
        f"Machine currently in use. Based on historical average session "
        f"duration of {avg_duration:.1f} minutes, estimated {time_remaining} "
        f"minutes remaining."
    )
    
    return False, time_remaining, message


def predict_machine_availability_future(
    machine_id: str,
    day: str,
    time: str
) -> Tuple[bool, int, str]:
    """Predict future machine availability based on historical patterns.
    
    Uses historical occupancy probability to estimate if machine will
    be available at the specified day/time.
    
    Args:
        machine_id: Machine identifier (e.g., "DC_BENCH_001")
        day: Day of week (e.g., "thursday")
        time: Time in HH:MM format (e.g., "14:00")
        
    Returns:
        Tuple of (available: bool, time_to_wait: int, message: str)
        
    Raises:
        ValueError: If machine_id is not found
    """
    db = load_simulated_db()
    
    # Verify machine exists
    sensor = get_sensor_for_machine(db, machine_id)
    if sensor is None:
        raise ValueError(f"Machine '{machine_id}' not found")
    
    sensor_id = sensor["sensor_id"]
    
    # Get historical occupancy probability
    occupancy_prob = get_historical_occupancy_probability(db, machine_id, day, time)
    
    # Determine if likely available
    likely_available = occupancy_prob < OCCUPANCY_PROBABILITY_THRESHOLD
    
    if likely_available:
        return True, 0, (
            f"Machine predicted to be available on {day} at {time}. "
            f"Historical occupancy rate: {occupancy_prob:.0%}"
        )
    
    # Machine likely occupied - estimate wait time based on avg session duration
    historical_durations = get_historical_set_durations(db, sensor_id)
    avg_duration = calculate_average_session_duration(historical_durations)
    
    # Estimate wait time: higher probability = longer potential wait
    # Scale wait time based on how far above threshold we are
    excess_prob = occupancy_prob - OCCUPANCY_PROBABILITY_THRESHOLD
    wait_multiplier = 1 + (excess_prob / (1 - OCCUPANCY_PROBABILITY_THRESHOLD))
    estimated_wait = int(round(avg_duration * wait_multiplier * 0.5))
    
    # Ensure reasonable wait time (at least 1, at most avg_duration)
    estimated_wait = max(1, min(int(avg_duration), estimated_wait))
    
    message = (
        f"Machine likely occupied on {day} at {time}. "
        f"Historical occupancy rate: {occupancy_prob:.0%}. "
        f"Estimated wait time: {estimated_wait} minutes."
    )
    
    return False, estimated_wait, message


def get_all_machines(db: Optional[dict] = None) -> list[str]:
    """Get list of all available machine IDs.
    
    Args:
        db: Simulated database dict (loads from file if None)
        
    Returns:
        List of machine IDs
    """
    if db is None:
        db = load_simulated_db()
    
    return [sensor["machine"] for sensor in db.get("sensors", [])]
