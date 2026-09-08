from dataclasses import dataclass
from datetime import time
import os

from dotenv import load_dotenv


TIMEFRAMES = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name, str(default)).strip().lower()
    if value not in {"true", "false"}:
        raise ValueError(f"{name} must be true or false")
    return value == "true"


def _clock(name: str, default: str) -> time:
    hour, minute = (int(part) for part in os.getenv(name, default).split(":"))
    return time(hour, minute)


@dataclass(frozen=True)
class Settings:
    symbols: tuple[str, ...] = ("EURUSD",)
    timeframe: str = "M15"
    poll_seconds: int = 60
    dry_run: bool = True
    live_trading_enabled: bool = False
    require_demo_account: bool = True
    risk_per_trade: float = 0.02
    max_open_positions: int = 2
    max_spread_points: float = 25
    session_start_utc: time = time(7, 0)
    session_end_utc: time = time(17, 0)
    magic_number: int = 260907
    deviation_points: int = 10
    mt5_path: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        symbols = tuple(s.strip().upper() for s in os.getenv("SYMBOLS", "EURUSD").split(",") if s.strip())
        settings = cls(
            symbols=symbols,
            timeframe=os.getenv("TIMEFRAME", "M15").upper(),
            poll_seconds=int(os.getenv("POLL_SECONDS", "60")),
            dry_run=_bool("DRY_RUN", True),
            live_trading_enabled=_bool("LIVE_TRADING_ENABLED", False),
            require_demo_account=_bool("REQUIRE_DEMO_ACCOUNT", True),
            risk_per_trade=float(os.getenv("RISK_PER_TRADE", "0.02")),
            max_open_positions=int(os.getenv("MAX_OPEN_POSITIONS", "2")),
            max_spread_points=float(os.getenv("MAX_SPREAD_POINTS", "25")),
            session_start_utc=_clock("SESSION_START_UTC", "07:00"),
            session_end_utc=_clock("SESSION_END_UTC", "17:00"),
            magic_number=int(os.getenv("MAGIC_NUMBER", "260907")),
            deviation_points=int(os.getenv("DEVIATION_POINTS", "10")),
            mt5_path=os.getenv("MT5_PATH") or None,
        )
        if not settings.symbols or settings.timeframe not in TIMEFRAMES:
            raise ValueError("SYMBOLS must be non-empty and TIMEFRAME must be a supported MT5 timeframe")
        if not 0 < settings.risk_per_trade <= 0.02:
            raise ValueError("RISK_PER_TRADE must be greater than 0 and at most 0.02")
        if settings.max_open_positions < 1 or settings.poll_seconds < 1:
            raise ValueError("MAX_OPEN_POSITIONS and POLL_SECONDS must be positive")
        if not settings.dry_run and not settings.live_trading_enabled:
            raise ValueError("LIVE_TRADING_ENABLED=true is required when DRY_RUN=false")
        return settings
