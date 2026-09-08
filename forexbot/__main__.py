import logging
import time
from datetime import datetime, timezone

from .config import Settings, TIMEFRAMES
from .execution import MT5Execution
from .risk import position_size, within_session
from .strategy import trend_signal

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def run_once(settings: Settings, broker: MT5Execution) -> None:
    if not within_session(datetime.now(timezone.utc), settings.session_start_utc, settings.session_end_utc):
        log.info("outside configured UTC trading session")
        return
    positions = broker.open_positions()
    bot_positions = [p for p in positions if getattr(p, "magic", None) == settings.magic_number]
    if len(positions) >= settings.max_open_positions:
        log.info("max open positions reached")
        return
    for symbol in settings.symbols:
        rates = broker.mt5.copy_rates_from_pos(symbol, TIMEFRAMES[settings.timeframe], 1, 100)
        if rates is None or len(rates) < 50:
            log.warning("insufficient data for %s", symbol)
            continue
        quote = broker.quote(symbol)
        if quote.spread_points > settings.max_spread_points:
            log.info("spread filter rejected %s (%.1f points)", symbol, quote.spread_points)
            continue
        if any(getattr(p, "symbol", None) == symbol for p in bot_positions):
            log.info("duplicate-order safeguard rejected %s", symbol)
            continue
        closes = [float(row["close"]) for row in rates]
        highs = [float(row["high"]) for row in rates]
        lows = [float(row["low"]) for row in rates]
        signal = trend_signal(closes, highs, lows, quote.ask)
        if signal is not None and signal.direction == "sell":
            signal = trend_signal(closes, highs, lows, quote.bid)
        if signal is None:
            continue
        info = broker.mt5.symbol_info(symbol)
        account = broker.mt5.account_info()
        account_value = float(account.equity or account.balance)
        volume = position_size(account_value, settings.risk_per_trade, signal.entry,
                               signal.stop_loss, info.trade_tick_size, info.trade_tick_value,
                               info.volume_min, info.volume_max, info.volume_step)
        if volume:
            broker.send(symbol, signal, volume)


def main() -> None:
    settings = Settings.from_env()
    broker = MT5Execution(settings)
    broker.connect()
    while True:
        run_once(settings, broker)
        time.sleep(settings.poll_seconds)


if __name__ == "__main__":
    main()
