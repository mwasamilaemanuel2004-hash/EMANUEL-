"""Generation-3: deep sweep on the 1h cache (no new downloads).

Varies horizon too (10 and 20 bars). simulate()/entries read
_optimize.HORIZON at call time, so patching it per batch works.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

import _optimize as o1  # noqa: E402
import _optimize2 as o2  # noqa: E402
from _optimize import load_cached, precompute, simulate  # noqa: E402
from _optimize2 import entries_breakout, entries_pullback  # noqa: E402


def main() -> None:
    tf = "1h"
    feat = precompute(load_cached(tf))
    results = []
    for horizon in (10, 20):
        o1.HORIZON = horizon
        o2.HORIZON = horizon
        for rr in (3.0, 4.0, 5.0):
            for mult in (2.0, 3.0, 4.0):
                for tthr in (0.6, 0.8, 1.5):
                    for cool in (0, 3, 6):
                        for pthr in (0.1, 0.3):
                            cfg = {"reward_risk": rr, "stop_atr_mult": mult,
                                   "trend_atr_threshold": tthr, "cooldown": cool,
                                   "pressure_threshold": pthr}
                            for engine, fn in (
                                ("pullback", entries_pullback),
                                ("breakout", entries_breakout),
                            ):
                                m = simulate(fn(feat, cfg), feat)
                                results.append({"tf": tf, "engine": engine, "horizon": horizon, **cfg, **m})
    (ROOT / "_sweep3_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    valid = [r for r in results if r["trades"] >= 40 and r["exp"] is not None]
    valid.sort(key=lambda r: r["exp"], reverse=True)
    print("=== GEN3 TOP 20 (1h, by expectancy_R) ===", flush=True)
    for r in valid[:20]:
        print(json.dumps(r), flush=True)
    positive = [r for r in valid if r["exp"] is not None and r["exp"] > 0]
    print(f"POSITIVE_EXPECTANCY_CONFIGS={len(positive)}", flush=True)
    for r in positive[:10]:
        print(json.dumps(r), flush=True)


if __name__ == "__main__":
    main()
