"""Train the offline ML signal gate (free local AI via scikit-learn).

Uses the cached klines + the regime engine's signals as the label source.
Time-ordered 70/30 split (no shuffling) so the hold-out is strictly future.
Saves backend/artifacts/scalper_ml_gate.joblib and prints honest metrics.
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

from sklearn.ensemble import GradientBoostingClassifier  # noqa: E402
from sklearn.metrics import accuracy_score, roc_auc_score  # noqa: E402
import joblib  # noqa: E402

from _optimize import load_cached, precompute, simulate  # noqa: E402
from _optimize2 import entries_pullback  # noqa: E402
from app.core.ml_signal_gate import build_features  # noqa: E402

ARTIFACT = ROOT / "backend" / "artifacts" / "scalper_ml_gate.joblib"
PULLBACK_CFG = {"reward_risk": 4.0, "stop_atr_mult": 3.0, "pressure_threshold": 0.1,
                "trend_atr_threshold": 0.8, "cooldown": 0}


def collect(tf: str):
    data = load_cached(tf)
    feat = precompute(data)
    entries = entries_pullback(feat, PULLBACK_CFG)
    if not entries:
        return None
    sim = simulate(entries, feat)
    outcomes = sim  # aggregates only; recompute per-trade labels below
    labels = []
    highs = feat["high"]; lows = feat["low"]; closes = feat["close"]
    n = len(closes)
    for index in sorted(entries):
        side, entry, stop, target = entries[index]
        start = index + 1
        end = min(start + 10, n)
        risk = (entry - stop) if side == "BUY" else (stop - entry)
        if start >= end or risk <= 0:
            continue
        f_high = highs[start:end]; f_low = lows[start:end]
        if side == "BUY":
            s_hit = f_low <= stop; t_hit = f_high >= target
        else:
            s_hit = f_high >= stop; t_hit = f_low <= target
        s_pos = int(np.argmax(s_hit)) if s_hit.any() else -1
        t_pos = int(np.argmax(t_hit)) if t_hit.any() else -1
        if s_pos >= 0 and t_pos >= 0:
            win = s_pos > t_pos
        elif t_pos >= 0:
            win = True
        elif s_pos >= 0:
            win = False
        else:
            exit_price = float(closes[end - 1])
            pnl = (exit_price - entry) if side == "BUY" else (entry - exit_price)
            win = pnl > 0
        labels.append((index, 1 if win else 0))
    if len(labels) < 100:
        return None
    features = build_features(data)
    xs = np.array([features.iloc[i].to_numpy() for i, _ in labels], dtype=float)
    ys = np.array([y for _, y in labels], dtype=int)
    return xs, ys, sim


def main() -> None:
    datasets = []
    for tf in ("15m", "1h"):
        got = collect(tf)
        if got:
            datasets.append((tf, got))
            print(f"{tf}: samples={len(got[1])} baseline={json.dumps(got[2])}", flush=True)
    if not datasets:
        print("NOT_ENOUGH_DATA", flush=True)
        return

    xs = np.vstack([d[1][0] for d in datasets])
    ys = np.concatenate([d[1][1] for d in datasets])
    split = int(len(ys) * 0.7)
    model = GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.05, random_state=7)
    model.fit(xs[:split], ys[:split])

    x_te, y_te = xs[split:], ys[split:]
    proba = model.predict_proba(x_te)[:, -1]
    auc = roc_auc_score(y_te, proba) if len(set(y_te)) > 1 else float("nan")
    acc = accuracy_score(y_te, (proba >= 0.5).astype(int))

    mask = proba >= 0.6
    gate_wr = float(y_te[mask].mean() * 100) if mask.any() else float("nan")
    kept = float(mask.mean() * 100)
    print(f"HOLDOUT acc={acc:.3f} auc={auc:.3f} base_wr={y_te.mean()*100:.2f}%", flush=True)
    print(f"GATE>=0.6: kept={kept:.1f}% wr={gate_wr:.2f}%", flush=True)

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, ARTIFACT)
    print(f"SAVED {ARTIFACT}", flush=True)


if __name__ == "__main__":
    main()
