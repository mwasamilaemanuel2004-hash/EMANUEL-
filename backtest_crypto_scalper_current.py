"""Current Yahoo intraday validation for CryptoScalperBot."""
import asyncio
import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))
from app.bots.crypto.scalper_bot import CryptoScalperBot

TIMEFRAMES = ("1m", "5m", "10m", "15m")


def load_data(timeframe: str) -> pd.DataFrame:
    source_interval = "5m" if timeframe == "10m" else timeframe
    period = "7d" if source_interval == "1m" else "60d"
    raw = yf.download(
        "BTC-USD", period=period, interval=source_interval,
        auto_adjust=False, progress=False, threads=False, timeout=20,
    )
    if isinstance(raw.columns, pd.MultiIndex):
        raw = raw.xs("BTC-USD", axis=1, level=1)
    raw.columns = [str(column).lower() for column in raw.columns]
    data = raw.dropna(subset=["open", "high", "low", "close", "volume"])
    if timeframe == "10m":
        data = data.resample("10min").agg({
            "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum",
        }).dropna()
    return data.tail(300)


async def run_timeframe(timeframe: str) -> dict:
    data = load_data(timeframe)
    bot = CryptoScalperBot({
        "timeframe": timeframe,
        "risk_per_trade_pct": 1.0,
        "start_background_tasks": False,
    })
    outcomes = []
    signals = 0
    horizon = 10
    for index in range(30, len(data) - horizon, 2):
        signal = await bot.analyze_market(data.iloc[: index + 1])
        if signal is None:
            continue
        signals += 1
        future = data.iloc[index + 1:index + 1 + horizon]
        entry = float(signal.entry)
        stop = float(signal.stop_loss)
        target = float(signal.take_profit)
        if signal.side == "BUY":
            stop_hit = future["low"].le(stop)
            target_hit = future["high"].ge(target)
            risk = entry - stop
            if risk <= 0:
                continue
            if stop_hit.any() and target_hit.any():
                value = -1.0 if stop_hit.idxmax() <= target_hit.idxmax() else 2.5
            elif stop_hit.any():
                value = -1.0
            elif target_hit.any():
                value = 2.5
            else:
                value = (float(future["close"].iloc[-1]) - entry) / risk
        else:
            stop_hit = future["high"].ge(stop)
            target_hit = future["low"].le(target)
            risk = stop - entry
            if risk <= 0:
                continue
            if stop_hit.any() and target_hit.any():
                value = -1.0 if stop_hit.idxmax() <= target_hit.idxmax() else 2.5
            elif stop_hit.any():
                value = -1.0
            elif target_hit.any():
                value = 2.5
            else:
                value = (entry - float(future["close"].iloc[-1])) / risk
        outcomes.append(float(value))

    wins = [value for value in outcomes if value > 0]
    losses = [value for value in outcomes if value <= 0]
    equity = pd.Series(outcomes).cumsum() if outcomes else pd.Series(dtype=float)
    drawdown = float((equity.cummax() - equity).max()) if not equity.empty else 0.0
    return {
        "source": "Yahoo Finance current",
        "symbol": "BTC-USD",
        "timeframe": timeframe,
        "rows": len(data),
        "start": str(data.index[0]) if not data.empty else None,
        "end": str(data.index[-1]) if not data.empty else None,
        "signals": signals,
        "trades": len(outcomes),
        "status": "VALIDATED" if outcomes else "NOT_VALIDATED_NO_TRADES",
        "win_rate_pct": round(len(wins) / len(outcomes) * 100, 2) if outcomes else None,
        "profit_factor": round(sum(wins) / abs(sum(losses)), 3) if losses else None,
        "expectancy_R": round(sum(outcomes) / len(outcomes), 4) if outcomes else None,
        "max_drawdown_R": round(drawdown, 4),
        "risk_per_trade_pct": 1.0,
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


async def main() -> None:
    results = {}
    requested = os.environ.get("SCALPER_TIMEFRAME")
    timeframes = (requested,) if requested else TIMEFRAMES
    for timeframe in timeframes:
        try:
            results[timeframe] = await run_timeframe(timeframe)
        except Exception as error:
            results[timeframe] = {"status": "ERROR", "error": str(error)}
        print(f"completed={timeframe}", flush=True)
    output = ROOT / "data" / "reports" / "crypto_scalper_current.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
