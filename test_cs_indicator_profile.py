import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "backend")

from app.core.cs_indicator_library import analyze_market_input, analyze_strategy_profile, ticks_to_ohlcv


def main() -> None:
    timestamps = pd.date_range("2026-01-01", periods=80, freq="min", tz="UTC")
    close = np.linspace(100.0, 120.0, len(timestamps))
    candles = pd.DataFrame({
        "open": close - 0.2,
        "high": close + 0.5,
        "low": close - 0.5,
        "close": close,
        "volume": np.ones(len(close)),
    }, index=timestamps)
    profile = analyze_strategy_profile(candles)
    assert profile.bias == "BUY"
    assert profile.regime == "trending"
    assert profile.recommended_strategy == "trend_follow"
    assert 0.0 < profile.risk_multiplier <= 1.0

    ticks = [{"timestamp": ts, "price": price, "volume": 1} for ts, price in zip(timestamps, close)]
    aggregated = ticks_to_ohlcv(ticks, "5min")
    assert len(aggregated) == 16
    assert set(["open", "high", "low", "close", "volume"]).issubset(aggregated.columns)
    tick_profile = analyze_market_input(ticks, mode="tick", timeframe="3min", lookback=20)
    candle_profile = analyze_market_input(candles, mode="ohlcv")
    assert tick_profile.data_mode == "tick"
    assert candle_profile.data_mode == "ohlcv"
    print("cs_indicator_profile=ok")


if __name__ == "__main__":
    main()
