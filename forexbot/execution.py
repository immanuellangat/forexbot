import logging
from dataclasses import dataclass

from .strategy import Signal

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Quote:
    bid: float
    ask: float
    point: float

    @property
    def spread_points(self) -> float:
        return (self.ask - self.bid) / self.point


class MT5Execution:
    def __init__(self, settings):
        self.settings = settings
        try:
            import MetaTrader5 as mt5
        except ImportError as exc:
            raise RuntimeError("MetaTrader5 is required to run the bot") from exc
        self.mt5 = mt5

    def connect(self) -> None:
        kwargs = {"timeout": 30_000}
        if self.settings.mt5_path:
            kwargs["path"] = self.settings.mt5_path
        if not self.mt5.initialize(**kwargs):
            error = self.mt5.last_error()
            path = self.settings.mt5_path or "the default MT5 terminal"
            raise RuntimeError(
                f"MT5 initialize failed for {path}: {error}. "
                "Open MT5 fully, log in, enable Algo Trading, and ensure Python "
                "and MT5 run at the same privilege level."
            )
        info = self.mt5.terminal_info()
        if info is None:
            raise RuntimeError(f"MT5 connected but terminal_info is unavailable: {self.mt5.last_error()}")
        if not self.settings.dry_run and self.settings.require_demo_account:
            account = self.mt5.account_info()
            demo_mode = getattr(self.mt5, "ACCOUNT_TRADE_MODE_DEMO", 0)
            if account is None:
                raise RuntimeError(f"Unable to inspect MT5 account mode: {self.mt5.last_error()}")
            if account.trade_mode != demo_mode:
                self.mt5.shutdown()
                raise RuntimeError("Live execution is restricted to a demo MT5 account by REQUIRE_DEMO_ACCOUNT=true")

    def quote(self, symbol: str) -> Quote:
        info = self.mt5.symbol_info(symbol)
        tick = self.mt5.symbol_info_tick(symbol)
        if info is None or tick is None or info.point <= 0:
            raise RuntimeError(f"no usable quote for {symbol}")
        return Quote(tick.bid, tick.ask, info.point)

    def open_positions(self) -> list:
        return list(self.mt5.positions_get() or [])

    def send(self, symbol: str, signal: Signal, volume: float) -> None:
        if self.settings.dry_run:
            log.info("DRY RUN: %s %s %.8f SL=%.5f TP=%.5f", symbol, signal.direction, volume, signal.stop_loss, signal.take_profit)
            return
        order_type = self.mt5.ORDER_TYPE_BUY if signal.direction == "buy" else self.mt5.ORDER_TYPE_SELL
        price = self.quote(symbol).ask if signal.direction == "buy" else self.quote(symbol).bid
        request = {
            "action": self.mt5.TRADE_ACTION_DEAL, "symbol": symbol, "volume": volume,
            "type": order_type, "price": price, "sl": signal.stop_loss, "tp": signal.take_profit,
            "deviation": self.settings.deviation_points, "magic": self.settings.magic_number,
            "comment": "forexbot", "type_time": self.mt5.ORDER_TIME_GTC, "type_filling": self.mt5.ORDER_FILLING_IOC,
        }
        result = self.mt5.order_send(request)
        if result is None or result.retcode != self.mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"order rejected for {symbol}: {result}")
