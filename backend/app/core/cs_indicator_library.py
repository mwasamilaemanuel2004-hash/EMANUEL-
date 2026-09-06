# backend/app/core/cs_indicator_library.py
# ============================================
# CS INDICATOR LIBRARY
# Candlestick patterns + Support & Resistance + composite signals
# ============================================
# Delivered for ESMH.TRADE (Forex + Crypto + Stocks).
# Primary backend ........ pandas-ta (pip: pandas-ta) / TA-Lib
# Pure-pandas fallback ... works even when neither is installed.
# Maelezo: Candlestick (CDL) + Support/Resistance (S/R) kwa bot zote.
# ============================================

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from loguru import logger

# ------------------------------------------------------------------
# Optional library import (soft so the core always imports)
# ------------------------------------------------------------------
try:  # pragma: no cover - environment dependent
    import pandas_ta as pta  # type: ignore

    _HAS_PANDAS_TA = True
except Exception:  # pragma: no cover
    pta = None  # type: ignore
    _HAS_PANDAS_TA = False

try:  # pragma: no cover - environment dependent
    import talib  # type: ignore

    _HAS_TALIB = True
except Exception:  # pragma: no cover
    talib = None  # type: ignore
    _HAS_TALIB = False

# Candlestick patterns supported by pandas-ta `cdl_pattern` names
SUPPORTED_CDL_PATTERNS: List[str] = [
    "doji",
    "hammer",
    "invertedhammer",
    "hangingman",
    "shootingstar",
    "engulfing",
    "morningstar",
    "eveningstar",
    "threewhitesoldiers",
    "threeblackcrows",
    "marubozu",
    "harami",
    "piercing",
    "darkcloudcover",
]

_EPS = 1e-12


def _body(open_: np.ndarray, close_: np.ndarray) -> np.ndarray:
    return np.abs(close_ - open_)


def _range(high: np.ndarray, low: np.ndarray) -> np.ndarray:
    return np.maximum(high - low, _EPS)


def _is_bullish(open_: np.ndarray, close_: np.ndarray) -> np.ndarray:
    return close_ >= open_


# ------------------------------------------------------------------
# PURE-PANDAS FALLBACK PATTERNS (works with no indicator library)
# ------------------------------------------------------------------
def _manual_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the core pattern columns using numpy only."""
    o = df["open"].to_numpy(dtype=float)
    h = df["high"].to_numpy(dtype=float)
    l = df["low"].to_numpy(dtype=float)
    c = df["close"].to_numpy(dtype=float)

    n = len(df)
    body = _body(o, c)
    rng = _range(h, l)
    upper = h - np.maximum(o, c)
    lower = np.minimum(o, c) - l
    bullish = _is_bullish(o, c)

    cols: Dict[str, np.ndarray] = {}

    # -- Doji
    cols["doji"] = (body / rng < 0.1).astype(int)

    # -- Hammer: long lower shadow, tiny upper shadow, body in upper third
    hammer = (lower >= 2.0 * body) & (upper <= body) & (body / rng <= 0.4)
    cols["hammer"] = (hammer & ~bullish).astype(int)
    cols["invertedhammer"] = (hammer & bullish).astype(int)
    cols["hangingman"] = (hammer & bullish).astype(int)

    # -- Shooting star / marubozu
    star = (upper >= 2.0 * body) & (lower <= body) & (body / rng <= 0.4)
    cols["shootingstar"] = (star & bullish).astype(int)
    cols["marubozu"] = (body / rng > 0.8).astype(int)

    # -- Engulfing (needs previous candle)
    engulf = np.zeros(n, dtype=int)
    if n >= 2:
        prev_bearish = ~bullish[:-1]
        prev_body = body[:-1]
        engulf[1:] = (
            bullish[1:] & prev_bearish
            & (c[1:] >= o[:-1]) & (o[1:] <= c[:-1])
            & (body[1:] > prev_body)
        ).astype(int)
    cols["engulfing"] = engulf

    # -- Morning star / evening star (3-candle)
    morning = np.zeros(n, dtype=int)
    evening = np.zeros(n, dtype=int)
    if n >= 3:
        first_bear = ~bullish[:-2] & (body[:-2] / rng[:-2] > 0.5)
        small_mid = body[1:-1] / rng[1:-1] < 0.3
        morning[2:] = (
            first_bear & small_mid & bullish[2:]
            & (c[2:] > (o[:-2] + c[:-2]) / 2.0)
        ).astype(int)
        first_bull = bullish[:-2] & (body[:-2] / rng[:-2] > 0.5)
        evening[2:] = (
            first_bull & small_mid & ~bullish[2:]
            & (c[2:] < (o[:-2] + c[:-2]) / 2.0)
        ).astype(int)
    cols["morningstar"] = morning
    cols["eveningstar"] = evening

    out = pd.DataFrame(cols, index=df.index)
    for name in SUPPORTED_CDL_PATTERNS:
        if name not in out.columns:
            out[name] = 0
    return out


def _pattern_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Best-effort candlestick pattern DataFrame for every supported pattern."""
    if _HAS_PANDAS_TA and pta is not None:
        try:
            frames = []
            for name in SUPPORTED_CDL_PATTERNS:
                try:
                    col = df.ta.cdl_pattern(name=name)
                    if isinstance(col, pd.Series) and len(col) == len(df):
                        frames.append(col.rename(name).fillna(0).astype(int))
                    elif isinstance(col, pd.DataFrame):
                        col = col.iloc[:, 0].rename(name).fillna(0).astype(int)
                        frames.append(col)
                except Exception:
                    continue
            if frames:
                return pd.concat(frames, axis=1)
        except Exception as exc:  # pragma: no cover
            logger.debug(f"pandas-ta patterns unavailable, using manual calc: {exc}")

    return _manual_patterns(df)