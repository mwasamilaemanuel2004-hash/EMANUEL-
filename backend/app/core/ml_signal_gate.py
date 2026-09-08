"""Local (offline) ML signal gate - free AI, no external API required.

Uses scikit-learn (already a project dependency) trained on locally cached
Binance klines via _train_ml_gate.py. The artifact is a small joblib file;
if it is missing or ml_enabled is False the gate falls back to its legacy
neutral score, so production behaviour never depends on the model.
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ARTIFACT_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "scalper_ml_gate.joblib"


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Causal per-bar features (no lookahead) used for training and scoring."""
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    open_ = df["open"].astype(float)
    volume = df["volume"].astype(float)
    prev_close = close.shift(1)
    true_range = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = true_range.rolling(14).mean()
    ema_fast = close.ewm(span=21, adjust=False).mean()
    ema_slow = close.ewm(span=55, adjust=False).mean()
    range_hi = high.rolling(20).max()
    range_lo = low.rolling(20).min()
    candle_range = (high - low).clip(lower=1e-12)
    vol_ma = volume.rolling(20).mean()
    features = pd.DataFrame({
        "candle_pressure": (close - open_) / candle_range,
        "body_ratio": (close - open_).abs() / candle_range,
        "atr_ratio": atr / close,
        "trend_strength": (ema_fast - ema_slow) / atr.replace(0.0, np.nan),
        "range_pos": (close - range_lo) / (range_hi - range_lo).clip(lower=1e-12),
        "vol_ratio": volume / vol_ma.replace(0.0, np.nan),
        "ret_1": close.pct_change(),
        "ret_5": close.pct_change(5),
    })
    return features.replace([np.inf, -np.inf], np.nan).fillna(0.0)


class LocalMLSignalGate:
    """Tiny offline sklearn gate. Returns win-probability or None."""

    def __init__(self, artifact_path=None):
        path = Path(artifact_path) if artifact_path else ARTIFACT_PATH
        self.model = None
        try:
            if path.exists():
                self.model = joblib.load(path)
        except Exception:
            self.model = None

    @property
    def ready(self) -> bool:
        return self.model is not None

    def score(self, feature_row: np.ndarray):
        if self.model is None:
            return None
        try:
            proba = self.model.predict_proba(np.asarray(feature_row, dtype=float).reshape(1, -1))[0]
            return float(proba[-1])
        except Exception:
            return None
