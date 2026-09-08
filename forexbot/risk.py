import math


def position_size(
    equity: float,
    risk_fraction: float,
    entry: float,
    stop_loss: float,
    tick_size: float,
    tick_value: float,
    volume_min: float,
    volume_max: float,
    volume_step: float,
) -> float:
    """Calculate volume from monetary stop risk, rounded down to broker step."""
    distance = abs(entry - stop_loss)
    if min(equity, risk_fraction, distance, tick_size, tick_value, volume_step) <= 0:
        raise ValueError("equity, risk, stop distance, tick settings, and volume step must be positive")
    raw = equity * risk_fraction / (distance / tick_size * tick_value)
    stepped = math.floor(raw / volume_step + 1e-9) * volume_step
    return round(max(volume_min, min(volume_max, stepped)), 8) if stepped >= volume_min else 0.0


def within_session(now_utc, start, end) -> bool:
    current = now_utc.time()
    return start <= current < end if start <= end else current >= start or current < end
