# Forexbot

Conservative, rule-based forex trend follower for MetaTrader 5. **Dry-run mode is
the default and live trading requires two explicit configuration gates.**

## Quick start

1. Install Python 3.11+ and MetaTrader 5 (the terminal must be running and
   logged in to a demo account for market data).
2. Install the package:

   ```powershell
   python -m pip install -e ".[dev]"
   ```

3. Copy `.env.example` to `.env`, review every value, and leave
   `DRY_RUN=true` while testing.
4. Run one polling cycle:

   ```powershell
   python -m forexbot
   ```

If connection fails with IPC timeout `-10005`, make sure the MT5 terminal is
fully open and logged in, then set `MT5_PATH` to its `terminal64.exe` path in
`.env`. Run Python and MT5 with the same Windows privilege level. The adapter
reports the selected path and MT5 error without attempting an order.

The bot reads closed candles only. The default strategy buys when EMA(20) is
above EMA(50), RSI(14) is between 50 and 70, and price is above EMA(20);
it sells on the symmetric conditions (RSI 30–50). ATR(14) sets a 2×ATR stop
and a 6×ATR target (a strict 1:3 risk-to-reward ratio). Entries are rejected outside the configured session, when
the spread is too wide, when a symbol already has a bot position, or when the
maximum position count is reached.

## Safety

`DRY_RUN=true` is mandatory by default: signals are logged and no order is
sent. Live execution is allowed only when `DRY_RUN=false` **and**
`LIVE_TRADING_ENABLED=true`; the process refuses to start otherwise.
`REQUIRE_DEMO_ACCOUNT=true` additionally blocks non-demo accounts. Use a demo
account first, set a small `RISK_PER_TRADE`, and verify symbol contract
settings with your broker. No credentials are stored by this project; MT5
uses the terminal's existing login.

Run tests with:

```powershell
python -m pytest
```