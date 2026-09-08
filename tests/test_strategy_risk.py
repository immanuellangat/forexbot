from datetime import datetime, time, timezone

import pytest

from forexbot.risk import position_size, within_session
from forexbot.strategy import trend_signal


def test_buy_signal_requires_aligned_uptrend():
    closes = [1 + i * 0.001 for i in range(46)]
    for index in range(14):
        closes.append(closes[-1] + (0.001 if index % 2 == 0 else -0.0005))
    highs = [value + 0.0005 for value in closes]
    lows = [value - 0.0005 for value in closes]
    signal = trend_signal(closes, highs, lows, closes[-1] + 0.0001)
    assert signal is not None and signal.direction == "buy"
    assert signal.take_profit > signal.entry > signal.stop_loss


def test_flat_market_has_no_signal():
    prices = [1.0] * 60
    assert trend_signal(prices, [1.001] * 60, [0.999] * 60, 1.0) is None


def test_signal_enforces_three_to_one_reward():
    from forexbot.strategy import Signal
    signal = Signal("sell", 1.1000, 1.1050, 1.0850, "test")
    assert signal.entry - signal.take_profit == pytest.approx(3 * (signal.stop_loss - signal.entry))
    with pytest.raises(ValueError, match="three times"):
        Signal("buy", 1.1000, 1.0950, 1.1101, "test")


def test_position_size_rounds_down_and_rejects_too_small():
    assert position_size(10_000, 0.01, 1.1, 1.095, 0.00001, 1.0, 0.01, 10, 0.01) == 0.2
    assert position_size(1, 0.001, 1.1, 1.095, 0.00001, 1.0, 0.01, 10, 0.01) == 0


def test_overnight_session_wraps_midnight():
    assert within_session(datetime(2026, 1, 1, 23, tzinfo=timezone.utc), time(22), time(2))
    assert not within_session(datetime(2026, 1, 1, 12, tzinfo=timezone.utc), time(22), time(2))


def test_live_mode_requires_explicit_gate(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "false")
    from forexbot.config import Settings
    with pytest.raises(ValueError, match="LIVE_TRADING_ENABLED"):
        Settings.from_env()


def test_default_risk_is_two_percent(monkeypatch):
    from forexbot.config import Settings
    monkeypatch.delenv("RISK_PER_TRADE", raising=False)
    monkeypatch.delenv("DRY_RUN", raising=False)
    monkeypatch.delenv("LIVE_TRADING_ENABLED", raising=False)
    assert Settings.from_env().risk_per_trade == 0.02
