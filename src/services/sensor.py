from datetime import datetime
from typing import Optional, Tuple
from src.models.sensor import SensorMetrics
from src.services.predictor import load_simulated_db

class SensorService:
    @staticmethod
    def get_metrics_for_period(machine_id: str, start_time: datetime, end_time: datetime) -> Optional[SensorMetrics]:
        """
        Retrieves sensor metrics for a specific machine within a time window.
        Returns None if no activity is found.
        Raises ValueError if machine/sensor doesn't exist.
        """
        
        db = load_simulated_db()  # !!!!! In a real app, it will be a chttp call to the sensor API
        
        # 1. Find Sensor
        target_sensor = None
        for s in db.get("sensors", []):
            if s["machine"] == machine_id:
                target_sensor = s
                break
        
        if not target_sensor:
            # Distinguish "Machine has no sensor" from "No data"
            raise ValueError(f"No sensor configured for machine {machine_id}")
            
        sensor_id = target_sensor["sensor_id"]
        
        # 2. Filter Sets (Optimized)
        # We need sets for this sensor
        sets = [s for s in db.get("set_summary", []) if s["sensor_id"] == sensor_id]
        
        if not sets:
             # Sensor exists but has zero history
             return None

        # 3. Strict Overlap Match
        matching_sets = []
        for s in sets:
            try:
                h_start = datetime.fromisoformat(s["start_time"].replace("Z", "+00:00"))
                h_end = datetime.fromisoformat(s["end_time"].replace("Z", "+00:00")) if s["end_time"] else start_time
                
                # Overlap: (StartA < EndB) and (EndA > StartB)
                if h_start < end_time and h_end > start_time:
                    overlap_start = max(h_start, start_time)
                    overlap_end = min(h_end, end_time)
                    overlap_duration = (overlap_end - overlap_start).total_seconds()
                    matching_sets.append((s, overlap_duration))
                    
            except (ValueError, TypeError):
                continue

        if not matching_sets:
            return None
            
        # 4. Pick Best Match (Max Overlap)
        matching_sets.sort(key=lambda x: x[1], reverse=True)
        sample = matching_sets[0][0]
        
        # 5. Map to Schema
        return SensorMetrics(
            total_reps=sample.get("total_reps", 0),
            total_time_under_tension=sample.get("total_time_under_tension", 0.0),
            avg_difficulty_level=sample.get("avg_difficulty_level", 0.0),
            speed_concentric_mean=sample.get("speed_concentric_mean", 0.0),
            speed_concentric_max=sample.get("speed_concentric_max", 0.0),
            amplitude_mean=sample.get("amplitude_mean", 0.0),
            amplitude_variability=sample.get("amplitude_variability", 0.0)
        )
