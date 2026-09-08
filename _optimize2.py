"""Generation-2 optimizer: breakout & pullback engines on higher TFs.

Reuses the stage-1 simulator. Mirrors the bot's 'breakout' and 'pullback'
entry paths exactly (prior 19-bar range for breakouts, EMA touch for
pullbacks), then validates the top configs through the real bot.
"""
import asyncio
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

from _optimize import (  # noqa: E402
    TIMEFRAMES, HORIZON, load_cached, precompute, simulate, run_real,
    regime_entries, legacy_entries,
)

G1_BEST = {"reward_risk": 2.5, "stop_atr_mult": 2.0, "pressure_threshold": 0.1,
           "trend_atr_threshold": 1.5, "reversion_extreme": 0.92, "cooldown": 0}


def entries_breakout(feat: dict, cfg: dict) -> dict:
    import pandas as pd
    close = feat["close"]; atr = feat["atr"]
    ema_fast = feat["ema_fast"]; ema_slow = feat["ema_slow"]
    pressure = feat["candle_pressure"]
    df_h = feat["high"]; df_l = feat["low"]
    prior_hi = pd.Series(df_h).rolling(19).max().shift(1).to_numpy()
    prior_lo = pd.Series(df_l).rolling(19).min().shift(1).to_numpy()
    n = len(close)
    last_signal = None
    rr = cfg["reward_risk"]; mult = cfg["stop_atr_mult"]
    tthr = cfg["trend_atr_threshold"]; cool = cfg["cooldown"]
    entries = {}
    for i in range(30, n - HORIZON, 2):
        a = atr[i]
        if not np.isfinite(a) or a <= 0 or a / close[i] >= 0.02:
            continue
        if cool > 0 and last_signal is not None and (i - last_signal) < cool:
            continue
        ts = (ema_fast[i] - ema_slow[i]) / a
        entry = close[i]
        side = None
        if ts > tthr * 0 and ts > 0 and close[i] > prior_hi[i] and np.isfinite(prior_hi[i]):
            side = "BUY"; stop = entry - a * mult; target = entry + a * mult * rr
        elif ts < 0 and close[i] < prior_lo[i] and np.isfinite(prior_lo[i]):
            side = "SELL"; stop = entry + a * mult; target = entry - a * mult * rr
        if side:
            entries[i] = (side, float(entry), float(stop), float(target))
            last_signal = i
    return entries


def entries_pullback(feat: dict, cfg: dict) -> dict:
    import pandas as pd
    close = feat["close"]; prev_close = feat["prev_close"]; atr = feat["atr"]
    ema_fast = feat["ema_fast"]; ema_slow = feat["ema_slow"]
    pressure = feat["candle_pressure"]
    df_h = feat["high"]; df_l = feat["low"]
    touched_lo = pd.Series(df_l).rolling(19).min().shift(1).to_numpy()
    touched_hi = pd.Series(df_h).rolling(19).max().shift(1).to_numpy()
    n = len(close)
    last_signal = None
    rr = cfg["reward_risk"]; mult = cfg["stop_atr_mult"]
    pthr = cfg["pressure_threshold"]; tthr = cfg["trend_atr_threshold"]
    cool = cfg["cooldown"]
    entries = {}
    for i in range(30, n - HORIZON, 2):
        a = atr[i]
        if not np.isfinite(a) or a <= 0 or a / close[i] >= 0.02:
            continue
        if cool > 0 and last_signal is not None and (i - last_signal) < cool:
            continue
        ts = (ema_fast[i] - ema_slow[i]) / a
        entry = close[i]
        side = None
        if ts > 0:
            if np.isfinite(touched_lo[i]) and touched_lo[i] <= ema_fast[i] \
                    and close[i] > prev_close[i] and pressure[i] > pthr:
                side = "BUY"; stop = entry - a * mult; target = entry + a * mult * rr
        elif ts < 0:
            if np.isfinite(touched_hi[i]) and touched_hi[i] >= ema_fast[i] \
                    and close[i] < prev_close[i] and pressure[i] < -pthr:
                side = "SELL"; stop = entry + a * mult; target = entry - a * mult * rr
        if side:
            entries[i] = (side, float(entry), float(stop), float(target))
            last_signal = i
    return entries


def sweep2() -> list:
    results = []
    timeframes = ("15m",)
    for tf in timeframes:
        feat = precompute(load_cached(tf))
        # Baselines
        m = simulate(regime_entries(feat, G1_BEST), feat)
        results.append({"tf": tf, "engine": "regime", **G1_BEST, **m})
        m = simulate(legacy_entries(feat, {"reward_risk": 2.5, "pressure_threshold": 0.1}), feat)
        results.append({"tf": tf, "engine": "legacy", "reward_risk": 2.5, "pressure_threshold": 0.1, **m})
        for rr in (2.0, 3.0, 4.0):
            for mult in (2.0, 3.0):
                for tthr in (0.8, 1.5):
                    for cool in (0, 3):
                        cfg = {"reward_risk": rr, "stop_atr_mult": mult, "pressure_threshold": 0.1,
                               "trend_atr_threshold": tthr, "cooldown": cool}
                        m = simulate(entries_breakout(feat, cfg), feat)
                        results.append({"tf": tf, "engine": "breakout", **cfg, **m})
                        for pthr in (0.1, 0.3):
                            cfgp = dict(cfg); cfgp["pressure_threshold"] = pthr
                            m = simulate(entries_pullback(feat, cfgp), feat)
                            results.append({"tf": tf, "engine": "pullback", **cfgp, **m})
    return results


async def main() -> None:
    results = sweep2()
    (ROOT / "_sweep2_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    valid = [r for r in results if r["trades"] >= 40 and r["exp"] is not None]
    valid.sort(key=lambda r: r["exp"], reverse=True)
    print("=== GEN2 TOP 15 (by expectancy_R) ===", flush=True)
    for r in valid[:15]:
        print(json.dumps(r), flush=True)
    print("=== GEN2 BOTTOM 3 ===", flush=True)
    for r in valid[-3:]:
        print(json.dumps(r), flush=True)

    print("=== GEN2 REAL-BOT VALIDATION (top 3 unique engine+cfg, home TF + 15m) ===", flush=True)
    seen = set()
    checked = 0
    for r in valid:
        if checked >= 3:
            break
        key = (r["engine"], r["reward_risk"], r.get("stop_atr_mult"), r["pressure_threshold"],
               r.get("trend_atr_threshold"), r.get("cooldown"))
        if key in seen:
            continue
        seen.add(key)
        checked += 1
        overrides = {
            "entry_strategy": r["engine"], "reward_risk": r["reward_risk"],
            "stop_atr_mult": r.get("stop_atr_mult", 1.5), "pressure_threshold": r["pressure_threshold"],
            "trend_atr_threshold": r.get("trend_atr_threshold", 1.0),
            "reversion_extreme": r.get("reversion_extreme", 0.9),
            "min_bars_between_trades": r.get("cooldown", 0),
        }
        for tf in (r["tf"], "15m"):
            real = await run_real(tf, overrides)
            print(json.dumps({"tf": tf, "stage": "REAL", "engine": r["engine"],
                              "reward_risk": r["reward_risk"], "stop_atr_mult": overrides["stop_atr_mult"],
                              "pressure_threshold": r["pressure_threshold"],
                              "trend_atr_threshold": overrides["trend_atr_threshold"],
                              "cooldown": overrides["min_bars_between_trades"], **real}), flush=True)


if __name__ == "__main__":
    asyncio.run(main())

