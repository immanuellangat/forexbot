# Forexbot

[![Tests](https://github.com/immanuellangat/forexbot/actions/workflows/tests.yml/badge.svg)](https://github.com/immanuellangat/forexbot/actions/workflows/tests.yml)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)

Conservative, rule-based forex trend follower for MetaTrader 5. **Dry-run mode is
the default and live trading requires two explicit configuration gates.**

> **Risk warning.** This is a learning project, not financial advice. Trading
> forex can lose money quickly. Test on a demo account first.

## How it works

Every `POLL_SECONDS` the bot runs one cycle for each configured symbol:

```text
closed candles ──▶ strategy ──▶ filters ──▶ position sizing ──▶ order (or a log line in dry-run)
   (MT5)          EMA/RSI/ATR    session,     risk % of equity      2×ATR stop, 6×ATR target
                                 spread,
                                 duplicates
```

| Step | Rule |
| --- | --- |
| **Data** | Closed candles only, so a signal never changes after the fact. |
| **Buy signal** | EMA(20) above EMA(50), price above EMA(20), RSI(14) between 50 and 70. |
| **Sell signal** | The mirror image: EMA(20) below EMA(50), price below EMA(20), RSI(14) between 30 and 50. |
| **Stop and target** | ATR(14) sets a 2×ATR stop and a 6×ATR target — a strict 1:3 risk-to-reward ratio. |
| **Filters** | No entry outside the configured session, when the spread is too wide, when the symbol already has a bot position, or when the maximum position count is reached. |
| **Position size** | Sized so that hitting the stop loses `RISK_PER_TRADE` of account equity, rounded down to the broker's volume step. |

## Quick start

1. Install Python 3.11+ and MetaTrader 5 (the terminal must be running and
   logged in to a demo account for market data). The bot itself runs on
   Windows, because the `MetaTrader5` Python package is Windows-only.
2. Install the package:

   ```powershell
   python -m pip install -e ".[dev]"
   ```

3. Copy `.env.example` to `.env`, review every value, and leave
   `DRY_RUN=true` while testing.
4. Start the bot (it polls until you stop it with <kbd>Ctrl</kbd>+<kbd>C</kbd>):

   ```powershell
   python -m forexbot
   ```

In dry-run mode a signal is logged instead of being sent, in this form:

```text
DRY RUN: <symbol> <buy|sell> <volume> SL=<stop price> TP=<target price>
```

## Configuration

All settings are read from `.env` (see `.env.example`).

| Setting | Default | Meaning |
| --- | --- | --- |
| `DRY_RUN` | `true` | Log signals instead of sending orders. |
| `LIVE_TRADING_ENABLED` | `false` | Second gate: must also be `true` before any order is sent. |
| `REQUIRE_DEMO_ACCOUNT` | `true` | Refuse to send orders on a non-demo account. |
| `SYMBOLS` | `EURUSD` | Comma-separated symbols to trade. |
| `TIMEFRAME` | `M15` | One of `M1`, `M5`, `M15`, `M30`, `H1`, `H4`, `D1`. |
| `POLL_SECONDS` | `60` | Seconds between polling cycles. |
| `RISK_PER_TRADE` | `0.02` | Fraction of equity risked per trade; values above `0.02` (2%) are rejected. |
| `MAX_OPEN_POSITIONS` | `2` | No new entries once this many positions are open. |
| `MAX_SPREAD_POINTS` | `25` | Skip a symbol while its spread is wider than this. |
| `SESSION_START_UTC` / `SESSION_END_UTC` | `07:00` / `17:00` | Trading window in UTC; it may run past midnight. |
| `MAGIC_NUMBER` | `260907` | Tag that identifies this bot's own positions. |
| `DEVIATION_POINTS` | `10` | Maximum price slippage accepted on an order. |
| `MT5_PATH` | unset | Path to `terminal64.exe`; set it when more than one terminal is installed. |

## Safety

`DRY_RUN=true` is mandatory by default: signals are logged and no order is
sent. Live execution is allowed only when `DRY_RUN=false` **and**
`LIVE_TRADING_ENABLED=true`; the process refuses to start otherwise.
`REQUIRE_DEMO_ACCOUNT=true` additionally blocks non-demo accounts. Use a demo
account first, set a small `RISK_PER_TRADE`, and verify symbol contract
settings with your broker. No credentials are stored by this project; MT5
uses the terminal's existing login.

## Troubleshooting

If connection fails with IPC timeout `-10005`, make sure the MT5 terminal is
fully open and logged in, then set `MT5_PATH` to its `terminal64.exe` path in
`.env`. Run Python and MT5 with the same Windows privilege level. The adapter
reports the selected path and MT5 error without attempting an order.

## Project layout

```text
forexbot/
  config.py      settings from .env, with validation and the live-trading gates
  strategy.py    EMA / RSI / ATR trend signal (pure functions, no broker needed)
  risk.py        position sizing and the trading-session check
  execution.py   MetaTrader 5 adapter: connect, quotes, positions, orders
  __main__.py    the polling loop
tests/           unit tests for the strategy, risk and configuration rules
```

## Tests

The strategy, risk and configuration logic have no broker dependency, so the
tests run on any operating system without MetaTrader 5:

```powershell
python -m pytest
```
