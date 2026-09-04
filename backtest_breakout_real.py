"""Real-data baseline for BreakoutBot using SPY daily candles."""
import asyncio
import sys

import pandas as pd
import yfinance as yf

sys.path.insert(0, "backend")
from app.bots.forex.breakout import BreakoutBot


def load_data() -> pd.DataFrame:
    raw = yf.download(
        "SPY",
        start="2022-01-01",
        end="2025-01-16",
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
        timeout=15,
    )
    data = raw.xs("SPY", axis=1, level=1) if isinstance(raw.columns, pd.MultiIndex) else raw
    data.columns = [str(column).lower() for column in data.columns]
    return data.dropna(subset=["open", "high", "low", "close", "volume"])


async def run() -> None:
    data = load_data()
    bot = BreakoutBot({"bot_id": "real_breakout_baseline"})
    outcomes = []
    signals = 0
    horizon = 10

    for index in range(60, len(data) - horizon):
        signal = await bot.analyze_market(data.iloc[: index + 1])
        if signal is None:
            continue
        signals += 1
        future = data.iloc[index + 1 : index + 1 + horizon]
        if signal.action == "BUY":
            hit_stop = future["low"].le(signal.stop_loss)
            hit_target = future["high"].ge(signal.take_profit)
            if hit_stop.any() and hit_target.any():
                result = -1.0 if hit_stop.idxmax() <= hit_target.idxmax() else 2.0
            elif hit_stop.any():
                result = -1.0
            elif hit_target.any():
                result = 2.0
            else:
                result = (future["close"].iloc[-1] - signal.entry_price) / (signal.entry_price - signal.stop_loss)
        else:
            hit_stop = future["high"].ge(signal.stop_loss)
            hit_target = future["low"].le(signal.take_profit)
            if hit_stop.any() and hit_target.any():
                result = -1.0 if hit_stop.idxmax() <= hit_target.idxmax() else 2.0
            elif hit_stop.any():
                result = -1.0
            elif hit_target.any():
                result = 2.0
            else:
                result = (signal.entry_price - future["close"].iloc[-1]) / (signal.stop_loss - signal.entry_price)
        outcomes.append(float(result))

    wins = [value for value in outcomes if value > 0]
    losses = [value for value in outcomes if value <= 0]
    equity = pd.Series(outcomes).cumsum() if outcomes else pd.Series(dtype=float)
    drawdown = (equity.cummax() - equity).max() if not equity.empty else 0.0
    profit_factor = sum(wins) / abs(sum(losses)) if losses else float("inf")
    win_rate = len(wins) / len(outcomes) * 100 if outcomes else 0.0
    print(f"rows={len(data)} period={data.index[0].date()}..{data.index[-1].date()}")
    print(f"signals={signals} trades={len(outcomes)} win_rate={win_rate:.2f}% profit_factor={profit_factor:.2f} max_dd_R={drawdown:.2f}")


if __name__ == "__main__":
    asyncio.run(run())
