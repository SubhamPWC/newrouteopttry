# Simple train speed/time stub (to be replaced with real APIs)
# Example: assume average speed and compute ETA for given great-circle distance.

AVG_TRAIN_SPEED_KMPH = 60.0  # configurable


def estimate_train_time_hours(distance_km: float, avg_speed_kmph: float = AVG_TRAIN_SPEED_KMPH) -> float:
    if avg_speed_kmph <= 0:
        return 0.0
    return round(distance_km / avg_speed_kmph, 2)
