from dataclasses import dataclass
import math
from typing import Literal


Direction = Literal["buy", "sell"]


@dataclass(frozen=True)
class Signal:
    direction: Direction
    entry: float
    stop_loss: float
    take_profit: float
    reason: str

    def __post_init__(self) -> None:
        stop_distance = abs(self.entry - self.stop_loss)
        target_distance = abs(self.take_profit - self.entry)
        if stop_distance <= 0 or not math.isclose(target_distance, 3 * stop_distance, rel_tol=1e-9, abs_tol=1e-8):
            raise ValueError("take-profit must be exactly three times the stop distance")
        if self.direction == "buy" and not (self.stop_loss < self.entry < self.take_profit):
            raise ValueError("buy signal levels must be stop < entry < target")
        if self.direction == "sell" and not (self.take_profit < self.entry < self.stop_loss):
            raise ValueError("sell signal levels must be target < entry < stop")


def _ema(values: list[float], period: int) -> float:
    if len(values) < period:
        raise ValueError("not enough candles for EMA")
    result = sum(values[:period]) / period
    multiplier = 2 / (period + 1)
    for value in values[period:]:
        result = (value - result) * multiplier + result
    return result


def _rsi(closes: list[float], period: int = 14) -> float:
    if len(closes) <= period:
        raise ValueError("not enough candles for RSI")
    changes = [b - a for a, b in zip(closes, closes[1:])]
    gains = [max(change, 0) for change in changes[-period:]]
    losses = [max(-change, 0) for change in changes[-period:]]
    average_loss = sum(losses) / period
    return 100.0 if average_loss == 0 else 100 - (100 / (1 + (sum(gains) / period) / average_loss))


def trend_signal(closes: list[float], highs: list[float], lows: list[float], entry: float) -> Signal | None:
    """Return a signal from closed candles, or None when conservative rules do not align."""
    if len(closes) < 50 or len(highs) != len(closes) or len(lows) != len(closes):
        raise ValueError("at least 50 aligned candles are required")
    fast, slow = _ema(closes, 20), _ema(closes, 50)
    rsi = _rsi(closes)
    atr = sum(high - low for high, low in zip(highs[-14:], lows[-14:])) / 14
    if atr <= 0:
        return None
    if fast > slow and entry > fast and 50 < rsi < 70:
        return Signal("buy", entry, entry - 2 * atr, entry + 6 * atr, "EMA20 > EMA50, price > EMA20, RSI 50-70")
    if fast < slow and entry < fast and 30 < rsi < 50:
        return Signal("sell", entry, entry + 2 * atr, entry - 6 * atr, "EMA20 < EMA50, price < EMA20, RSI 30-50")
    return None
