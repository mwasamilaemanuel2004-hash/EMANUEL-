"""Two-stage scalper optimizer.

Stage 1: fast vectorized sweep that mirrors the bot's regime engine formulas
         exactly (causal indicators only), scoring expectancy/PF on cached
         Binance klines.
Stage 2: re-runs the top configs through the REAL CryptoScalperBot
         (analyze_market) with the same simulation as the official backtest.
"""
import asyncio
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))
from app.bots.crypto.scalper_bot import CryptoScalperBot  # noqa: E402

import backtest_crypto_scalper_current as bt  # noqa: E402

FEE_RATE = 0.0004
HORIZON = 10
TIMEFRAMES = ("5m", "15m")


def load_cached(timeframe: str) -> pd.DataFrame:
    cache = ROOT / f"_cache_{timeframe}.csv"
    if cache.exists():
        return pd.read_csv(cache, index_col=0, parse_dates=True)
    data = bt.load_data(timeframe)
    data.to_csv(cache)
    return data


def precompute(data: pd.DataFrame) -> dict:
    close = data["close"].astype(float)
    high = data["high"].astype(float)
    low = data["low"].astype(float)
    open_ = data["open"].astype(float)
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    candle_range = (high - open_).abs()
    return {
        "open": open_.to_numpy(), "high": high.to_numpy(), "low": low.to_numpy(),
        "close": close.to_numpy(), "prev_close": prev_close.to_numpy(),
        "atr": tr.rolling(14).mean().to_numpy(),
        "ema_fast": close.ewm(span=21, adjust=False).mean().to_numpy(),
        "ema_slow": close.ewm(span=55, adjust=False).mean().to_numpy(),
        "range_hi": high.rolling(20).max().to_numpy(), "range_lo": low.rolling(20).min().to_numpy(),
        "candle_pressure": ((close - open_) / candle_range.clip(lower=1e-12)).to_numpy(),
        "index": data.index,
    }


def simulate(entries: dict, feat: dict) -> dict:
    """entries: {bar_index: (side, entry, stop, target)} -> backtest metrics."""
    outcomes = []
    high = feat["high"]; low = feat["low"]; close = feat["close"]
    n = len(close)
    for index in sorted(entries):
        side, entry, stop, target = entries[index]
        start = index + 1
        end = min(start + HORIZON, n)
        if start >= end:
            continue
        risk = (entry - stop) if side == "BUY" else (stop - entry)
        if risk <= 0:
            continue
        target_reward = abs(target - entry) / risk
        f_high = high[start:end]; f_low = low[start:end]
        if side == "BUY":
            stop_hit = f_low <= stop
            target_hit = f_high >= target
        else:
            stop_hit = f_high >= stop
            target_hit = f_low <= target
        s_pos = int(np.argmax(stop_hit)) if stop_hit.any() else -1
        t_pos = int(np.argmax(target_hit)) if target_hit.any() else -1
        if s_pos >= 0 and t_pos >= 0:
            stop_first = s_pos <= t_pos
            exit_price = stop if stop_first else target
            value = -1.0 if stop_first else target_reward
        elif s_pos >= 0:
            exit_price = stop
            value = -1.0
        elif t_pos >= 0:
            exit_price = target
            value = target_reward
        else:
            exit_price = float(close[end - 1])
            value = ((exit_price - entry) if side == "BUY" else (entry - exit_price)) / risk
        value -= ((entry + exit_price) * FEE_RATE) / risk
        outcomes.append(float(value))

    if not outcomes:
        return {"trades": 0, "pf": None, "exp": None, "dd": None, "wr": None}
    arr = np.array(outcomes)
    wins = arr[arr > 0]; losses = arr[arr <= 0]
    equity = np.cumsum(arr)
    dd = float((np.maximum.accumulate(equity) - equity).max())
    return {
        "trades": len(arr),
        "pf": round(float(wins.sum() / abs(losses.sum())), 3) if len(losses) else None,
        "exp": round(float(arr.mean()), 4),
        "dd": round(dd, 3),
        "wr": round(float(len(wins) / len(arr) * 100), 2),
    }


def regime_entries(feat: dict, cfg: dict) -> dict:
    entries = {}
    close = feat["close"]; prev_close = feat["prev_close"]; atr = feat["atr"]
    ema_fast = feat["ema_fast"]; ema_slow = feat["ema_slow"]
    range_hi = feat["range_hi"]; range_lo = feat["range_lo"]
    pressure = feat["candle_pressure"]
    n = len(close)
    last_signal = None
    rr = cfg["reward_risk"]; mult = cfg["stop_atr_mult"]
    pthr = cfg["pressure_threshold"]; tthr = cfg["trend_atr_threshold"]
    rev = cfg["reversion_extreme"]; cooldown = cfg["cooldown"]
    for i in range(30, n - HORIZON, 2):
        a = atr[i]
        if not np.isfinite(a) or a <= 0 or a / close[i] >= 0.02:
            continue
        if cooldown > 0 and last_signal is not None and (i - last_signal) < cooldown:
            continue
        ts = (ema_fast[i] - ema_slow[i]) / a
        rng = range_hi[i] - range_lo[i]
        rpos = (close[i] - range_lo[i]) / max(rng, 1e-12)
        side = None
        entry = close[i]
        if abs(ts) >= tthr:
            if ts > 0 and close[i] > prev_close[i] and pressure[i] > pthr:
                side = "BUY"; stop = entry - a * mult; target = entry + a * mult * rr
            elif ts < 0 and close[i] < prev_close[i] and pressure[i] < -pthr:
                side = "SELL"; stop = entry + a * mult; target = entry - a * mult * rr
        else:
            if rpos >= rev and pressure[i] < 0:
                side = "SELL"; stop = entry + a * mult; target = entry - a * mult * rr
            elif rpos <= (1.0 - rev) and pressure[i] > 0:
                side = "BUY"; stop = entry - a * mult; target = entry + a * mult * rr
        if side:
            entries[i] = (side, float(entry), float(stop), float(target))
            last_signal = i
    return entries


def legacy_entries(feat: dict, cfg: dict) -> dict:
    entries = {}
    close = feat["close"]; prev_close = feat["prev_close"]; pressure = feat["candle_pressure"]
    high = feat["high"]; low = feat["low"]
    n = len(close)
    rr = cfg["reward_risk"]; pthr = cfg["pressure_threshold"]
    for i in range(30, n - HORIZON, 2):
        vol_ok = (high[i] - low[i]) / close[i] < 0.02
        risk_distance = max(abs(close[i] * 0.003), 1.0)
        if close[i] > prev_close[i] and abs(pressure[i]) > pthr and vol_ok:
            entries[i] = ("BUY", float(close[i]), float(close[i] - risk_distance), float(close[i] + risk_distance * rr))
        elif close[i] < prev_close[i] and abs(pressure[i]) > pthr and vol_ok:
            entries[i] = ("SELL", float(close[i]), float(close[i] + risk_distance), float(close[i] - risk_distance * rr))
    return entries


def sweep() -> list:
    grid_rr = (1.0, 1.5, 2.0, 2.5, 3.0)
    grid_mult = (1.0, 1.5, 2.0)
    grid_pthr = (0.10, 0.30, 0.50)
    grid_tthr = (0.8, 1.5)
    grid_rev = (0.85, 0.92)
    grid_cool = (0, 3)
    results = []
    for tf in TIMEFRAMES:
        feat = precompute(load_cached(tf))
        for rr in (1.0, 2.5):
            for pthr in (0.10, 0.30):
                m = simulate(legacy_entries(feat, {"reward_risk": rr, "pressure_threshold": pthr}), feat)
                results.append({"tf": tf, "engine": "legacy", "reward_risk": rr, "pressure_threshold": pthr, **m})
        for rr in grid_rr:
            for mult in grid_mult:
                for pthr in grid_pthr:
                    for tthr in grid_tthr:
                        for rev in grid_rev:
                            for cool in grid_cool:
                                cfg = {"reward_risk": rr, "stop_atr_mult": mult, "pressure_threshold": pthr,
                                       "trend_atr_threshold": tthr, "reversion_extreme": rev, "cooldown": cool}
                                m = simulate(regime_entries(feat, cfg), feat)
                                results.append({"tf": tf, "engine": "regime", **cfg, **m})
    return results


async def run_real(tf: str, overrides: dict) -> dict:
    data = load_cached(tf)
    bot = CryptoScalperBot({
        "timeframe": tf, "risk_mode": "balanced", "risk_per_trade_pct": 1.0,
        "start_background_tasks": False, "debug_errors": True, **overrides,
    })
    entries = {}
    for index in range(30, len(data) - HORIZON, 2):
        signal = await bot.analyze_market(data.iloc[: index + 1])
        if signal is not None:
            entries[index] = (signal.side, float(signal.entry), float(signal.stop_loss), float(signal.take_profit))
    feat = precompute(data)
    return simulate(entries, feat)


async def main() -> None:
    results = sweep()
    (ROOT / "_sweep_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    valid = [r for r in results if r["trades"] >= 30 and r["exp"] is not None]
    valid.sort(key=lambda r: r["exp"], reverse=True)
    print("=== STAGE 1 TOP 15 (by expectancy_R) ===", flush=True)
    for r in valid[:15]:
        print(json.dumps(r), flush=True)
    print("=== STAGE 1 BOTTOM 3 ===", flush=True)
    for r in valid[-3:]:
        print(json.dumps(r), flush=True)

    print("=== STAGE 2 REAL-BOT VALIDATION (top 4 unique configs on 5m + 15m) ===", flush=True)
    seen = set()
    checked = 0
    for r in valid:
        if r["engine"] != "regime" or checked >= 4:
            continue
        key = (r["reward_risk"], r["stop_atr_mult"], r["pressure_threshold"],
               r["trend_atr_threshold"], r["reversion_extreme"], r["cooldown"])
        if key in seen:
            continue
        seen.add(key)
        checked += 1
        overrides = {
            "entry_strategy": "regime", "reward_risk": r["reward_risk"],
            "stop_atr_mult": r["stop_atr_mult"], "pressure_threshold": r["pressure_threshold"],
            "trend_atr_threshold": r["trend_atr_threshold"], "reversion_extreme": r["reversion_extreme"],
            "min_bars_between_trades": r["cooldown"],
        }
        for tf in TIMEFRAMES:
            real = await run_real(tf, overrides)
            print(json.dumps({"tf": tf, "stage": "REAL", "reward_risk": r["reward_risk"],
                              "stop_atr_mult": r["stop_atr_mult"], "pressure_threshold": r["pressure_threshold"],
                              "trend_atr_threshold": r["trend_atr_threshold"],
                              "reversion_extreme": r["reversion_extreme"], "cooldown": r["cooldown"], **real}), flush=True)


if __name__ == "__main__":
    asyncio.run(main())


