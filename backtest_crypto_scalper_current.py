"""Public Binance intraday validation for CryptoScalperBot."""
import asyncio
import json
import sys
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))
from app.bots.crypto.scalper_bot import CryptoScalperBot

TIMEFRAMES = ("1m", "5m", "10m", "15m")
BINANCE_URL = "https://api.binance.com/api/v3/klines"
BINANCE_SYMBOL = "BTCUSDT"
MAX_BARS = 10000


def load_data(timeframe: str) -> pd.DataFrame:
    source_interval = "5m" if timeframe == "10m" else timeframe
    rows = []
    end_time = None
    while len(rows) < MAX_BARS:
        params = {"symbol": BINANCE_SYMBOL, "interval": source_interval, "limit": 1000}
        if end_time is not None:
            params["endTime"] = end_time
        response = requests.get(BINANCE_URL, params=params, timeout=20)
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        rows = batch + rows
        oldest_open = int(batch[0][0])
        next_end = oldest_open - 1
        if end_time == next_end:
            break
        end_time = next_end
        if len(batch) < 1000:
            break
        time.sleep(0.05)

    rows = rows[-MAX_BARS:]
    data = pd.DataFrame(rows, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_buy_volume",
        "taker_buy_quote_volume", "ignore",
    ])
    data.index = pd.to_datetime(data.pop("open_time"), unit="ms", utc=True)
    for column in ("open", "high", "low", "close", "volume"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=["open", "high", "low", "close", "volume"])
    if timeframe == "10m":
        data = data.resample("10min").agg({
            "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum",
        }).dropna()
    return data


def compute_streaks(outcomes: list) -> dict:
    """Profit-streak reporting derived from the R-based trade outcomes list."""
    max_wins = max_losses = 0
    current_wins = current_losses = 0
    for value in outcomes:
        if value > 0:
            current_wins += 1
            current_losses = 0
            max_wins = max(max_wins, current_wins)
        else:
            current_losses += 1
            current_wins = 0
            max_losses = max(max_losses, current_losses)
    return {
        "max_win_streak": max_wins,
        "max_loss_streak": max_losses,
        "current_win_streak": current_wins,
        "current_loss_streak": current_losses,
    }


async def run_timeframe(timeframe: str, risk_mode: str = "balanced",
                        risk_pct: float = 1.0) -> dict:
    data = load_data(timeframe)
    bot = CryptoScalperBot({
        "timeframe": timeframe,
        "risk_mode": risk_mode,
        "risk_per_trade_pct": risk_pct,
        "start_background_tasks": False,
        "debug_errors": True,
        "reward_risk": 1.0,
        "pressure_threshold": 0.10,
    })
    outcomes = []
    signals = 0
    long_trades = 0
    short_trades = 0
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
        fee_rate = 0.0004
        if signal.side == "BUY":
            stop_hit = future["low"].le(stop)
            target_hit = future["high"].ge(target)
            risk = entry - stop
            if risk <= 0:
                continue
            target_reward = abs(target - entry) / risk
            if stop_hit.any() and target_hit.any():
                stop_first = stop_hit.idxmax() <= target_hit.idxmax()
                exit_price = stop if stop_first else target
                value = -1.0 if stop_first else target_reward
            elif stop_hit.any():
                exit_price = stop
                value = -1.0
            elif target_hit.any():
                exit_price = target
                value = target_reward
            else:
                exit_price = float(future["close"].iloc[-1])
                value = (exit_price - entry) / risk
        else:
            stop_hit = future["high"].ge(stop)
            target_hit = future["low"].le(target)
            risk = stop - entry
            if risk <= 0:
                continue
            target_reward = abs(target - entry) / risk
            if stop_hit.any() and target_hit.any():
                stop_first = stop_hit.idxmax() <= target_hit.idxmax()
                exit_price = stop if stop_first else target
                value = -1.0 if stop_first else target_reward
            elif stop_hit.any():
                exit_price = stop
                value = -1.0
            elif target_hit.any():
                exit_price = target
                value = target_reward
            else:
                exit_price = float(future["close"].iloc[-1])
                value = (entry - exit_price) / risk
        value -= ((entry + exit_price) * fee_rate) / risk
        outcomes.append(float(value))
        if signal.side == "BUY":
            long_trades += 1
        else:
            short_trades += 1

    wins = [value for value in outcomes if value > 0]
    losses = [value for value in outcomes if value <= 0]
    equity = pd.Series(outcomes).cumsum() if outcomes else pd.Series(dtype=float)
    drawdown = float((equity.cummax() - equity).max()) if not equity.empty else 0.0
    streaks = compute_streaks(outcomes)
    # Capital-exposure reporting: every trade risks `risk_pct` of capital, so a
    # worst equity drawdown of N R-units equals N * risk_pct of the capital that
    # was exposed to loss; the worst loss-streak bounds that exposure the same way.
    capital_exposure_pct = round(drawdown * risk_pct, 4)
    worst_streak_exposure_pct = round(streaks["max_loss_streak"] * risk_pct, 4)
    return {
        "source": "Binance public klines",
        "symbol": BINANCE_SYMBOL,
        "timeframe": timeframe,
        "rows": len(data),
        "start": str(data.index[0]) if not data.empty else None,
        "end": str(data.index[-1]) if not data.empty else None,
        "signals": signals,
        "trades": len(outcomes),
        "trade_count": len(outcomes),
        "long_trades": long_trades,
        "short_trades": short_trades,
        "status": "VALIDATED" if outcomes else "NOT_VALIDATED_NO_TRADES",
        "win_rate_pct": round(len(wins) / len(outcomes) * 100, 2) if outcomes else None,
        "profit_factor": round(sum(wins) / abs(sum(losses)), 3) if losses else None,
        "expectancy_R": round(sum(outcomes) / len(outcomes), 4) if outcomes else None,
        "max_drawdown_R": round(drawdown, 4),
        "max_win_streak": streaks["max_win_streak"],
        "max_loss_streak": streaks["max_loss_streak"],
        "current_win_streak": streaks["current_win_streak"],
        "current_loss_streak": streaks["current_loss_streak"],
        "capital_exposure_pct": capital_exposure_pct,
        "worst_streak_exposure_pct": worst_streak_exposure_pct,
        "risk_per_trade_pct": risk_pct,
        "fee_rate": fee_rate,
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


async def run_risk_modes(timeframe: str = "5m") -> dict:
    """Compare risk profiles without changing signal selection."""
    results = {}
    for mode, risk_pct in (("low", 0.5), ("balanced", 1.0), ("high", 2.0)):
        result = await run_timeframe(timeframe, mode, risk_pct)
        result["risk_mode"] = mode
        result["configured_risk_per_trade_pct"] = risk_pct
        results[mode] = result
    return results


async def main() -> None:
    results = {}
    requested = os.environ.get("SCALPER_TIMEFRAME")
    timeframes = (requested,) if requested else TIMEFRAMES
    for timeframe in timeframes:
        try:
            results[timeframe] = await run_risk_modes(timeframe)
        except Exception as error:
            results[timeframe] = {"status": "ERROR", "error": str(error)}
        print(f"completed={timeframe}", flush=True)
    output = ROOT / "data" / "reports" / "crypto_scalper_current.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
