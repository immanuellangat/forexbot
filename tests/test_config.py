from datetime import datetime, time, timezone

import pytest

from forexbot.config import Settings
from forexbot.risk import within_session

ENV_NAMES = (
    "SYMBOLS", "TIMEFRAME", "POLL_SECONDS", "DRY_RUN", "LIVE_TRADING_ENABLED", "REQUIRE_DEMO_ACCOUNT",
    "RISK_PER_TRADE", "MAX_OPEN_POSITIONS", "MAX_SPREAD_POINTS", "SESSION_START_UTC", "SESSION_END_UTC",
    "MAGIC_NUMBER", "DEVIATION_POINTS", "MT5_PATH",
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    """Start every test from an empty environment, away from any local .env file."""
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("forexbot.config.load_dotenv", lambda: None)


def test_defaults_are_dry_run_and_demo_only():
    settings = Settings.from_env()
    assert settings.dry_run is True
    assert settings.live_trading_enabled is False
    assert settings.require_demo_account is True


def test_live_trading_needs_both_gates(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "false")
    with pytest.raises(ValueError, match="LIVE_TRADING_ENABLED"):
        Settings.from_env()
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "true")
    assert Settings.from_env().dry_run is False


@pytest.mark.parametrize("risk", ["0", "-0.01", "0.021", "1"])
def test_risk_per_trade_is_capped_at_two_percent(monkeypatch, risk):
    monkeypatch.setenv("RISK_PER_TRADE", risk)
    with pytest.raises(ValueError, match="RISK_PER_TRADE"):
        Settings.from_env()


def test_booleans_must_be_spelled_out(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "yes")
    with pytest.raises(ValueError, match="DRY_RUN"):
        Settings.from_env()


def test_unknown_timeframe_is_rejected(monkeypatch):
    monkeypatch.setenv("TIMEFRAME", "M2")
    with pytest.raises(ValueError, match="TIMEFRAME"):
        Settings.from_env()


def test_symbols_are_trimmed_and_upper_cased(monkeypatch):
    monkeypatch.setenv("SYMBOLS", " eurusd , gbpusd ,")
    assert Settings.from_env().symbols == ("EURUSD", "GBPUSD")


def _at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 1, 5, hour, minute, tzinfo=timezone.utc)


def test_session_start_is_inclusive_and_end_is_exclusive():
    assert within_session(_at(7), time(7), time(17))
    assert within_session(_at(16, 59), time(7), time(17))
    assert not within_session(_at(17), time(7), time(17))
    assert not within_session(_at(6, 59), time(7), time(17))

