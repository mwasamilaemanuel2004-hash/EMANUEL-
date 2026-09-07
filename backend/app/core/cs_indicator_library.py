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
from dataclasses import dataclass, asdict
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


@dataclass(frozen=True)
class StrategyProfile:
    """Explainable market profile shared by every strategy family."""

    regime: str
    bias: str
    recommended_strategy: str
    confidence: float
    volatility_pct: float
    trend_strength: float
    momentum: float
    support: float
    resistance: float
    risk_multiplier: float
    explanation: str
    data_mode: str = "ohlcv"

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def ticks_to_ohlcv(ticks: List[Dict[str, Any]], timeframe: str = "1min") -> pd.DataFrame:
    """Aggregate broker/exchange ticks into validated OHLCV candles."""
    if not ticks:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    frame = pd.DataFrame(ticks)
    required = {"price"}
    if not required.issubset(frame.columns):
        raise ValueError("ticks require a price field")
    if "timestamp" not in frame.columns:
        frame["timestamp"] = pd.Timestamp.utcnow()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    frame["price"] = pd.to_numeric(frame["price"], errors="coerce")
    volume = frame["volume"] if "volume" in frame.columns else pd.Series(0.0, index=frame.index)
    frame["volume"] = pd.to_numeric(volume, errors="coerce").fillna(0.0)
    frame = frame.dropna(subset=["timestamp", "price"])
    frame = frame[frame["price"] > 0].set_index("timestamp").sort_index()
    if frame.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    return frame["price"].resample(timeframe).ohlc().join(
        frame["volume"].resample(timeframe).sum()
    ).dropna(subset=["open", "high", "low", "close"])


def analyze_strategy_profile(df: pd.DataFrame, lookback: int = 50) -> StrategyProfile:
    """Classify regime and return conservative strategy/risk guidance."""
    required = {"open", "high", "low", "close"}
    if not required.issubset(df.columns) or len(df) < max(20, lookback):
        raise ValueError(f"OHLC data with at least {max(20, lookback)} rows is required")
    close = pd.to_numeric(df["close"], errors="coerce").dropna()
    high = pd.to_numeric(df["high"], errors="coerce").reindex(close.index)
    low = pd.to_numeric(df["low"], errors="coerce").reindex(close.index)
    if len(close) < max(20, lookback) or (close <= 0).any():
        raise ValueError("OHLC prices must be positive and complete")
    fast = close.ewm(span=max(5, lookback // 2), adjust=False).mean()
    slow = close.ewm(span=lookback, adjust=False).mean()
    returns = close.pct_change().dropna()
    volatility_pct = float(returns.tail(lookback).std(ddof=0) * 100)
    momentum = float((close.iloc[-1] / close.iloc[-min(10, len(close))]) - 1)
    trend_strength = float(abs(fast.iloc[-1] - slow.iloc[-1]) / max(close.iloc[-1], _EPS))
    support = float(low.tail(lookback).min())
    resistance = float(high.tail(lookback).max())
    direction = "BUY" if fast.iloc[-1] > slow.iloc[-1] else "SELL" if fast.iloc[-1] < slow.iloc[-1] else "HOLD"
    if volatility_pct > 1.5:
        regime, strategy, risk = "high_volatility", "breakout", 0.5
    elif trend_strength > 0.002:
        regime, strategy, risk = "trending", "trend_follow", 1.0
    else:
        regime, strategy, risk = "ranging", "mean_reversion", 0.7
    confidence = min(0.95, max(0.5, 0.5 + trend_strength * 20 + min(abs(momentum) * 5, 0.25)))
    if regime == "high_volatility":
        confidence = min(confidence, 0.75)
    explanation = f"{regime}: {direction} bias, volatility {volatility_pct:.3f}%, strategy {strategy}"
    return StrategyProfile(
        regime=regime, bias=direction, recommended_strategy=strategy,
        confidence=round(confidence, 4), volatility_pct=round(volatility_pct, 6),
        trend_strength=round(trend_strength, 6), momentum=round(momentum, 6),
        support=round(support, 8), resistance=round(resistance, 8),
        risk_multiplier=risk, explanation=explanation,
    )


def analyze_market_input(data: Any, mode: str = "ohlcv", *, timeframe: str = "1min",
                         lookback: int = 50) -> StrategyProfile:
    """Analyze user-selected tick or OHLCV input through one safe interface."""
    normalized_mode = str(mode).strip().lower()
    if normalized_mode == "tick":
        frame = ticks_to_ohlcv(data, timeframe=timeframe)
    elif normalized_mode in {"ohlcv", "candle", "candles"}:
        if not isinstance(data, pd.DataFrame):
            frame = pd.DataFrame(data)
        else:
            frame = data.copy()
    else:
        raise ValueError("mode must be 'tick' or 'ohlcv'")
    profile = analyze_strategy_profile(frame, lookback=lookback)
    return StrategyProfile(**{**profile.as_dict(), "data_mode": normalized_mode})


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
