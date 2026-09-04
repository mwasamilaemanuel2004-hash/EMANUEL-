"""Repeatable real-data smoke backtest for BaseBot-compatible strategies."""
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import yfinance as yf
from loguru import logger

logger.remove()

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

from app.bots.base_bot import BaseBot
from app.bots.commodities_bot import CommoditiesBot
from app.bots.crypto.dca_bot import DcaBot
from app.bots.crypto.tokenization_bot import TokenizationBot
from app.bots.forex.breakout import BreakoutBot
from app.bots.forex.forex_scapler import ForexScalperBot
from app.bots.forex.news_bot import NewsBot
from app.bots.forex.smart_money import SmartMoneyBot
from app.bots.forex.trend_follower import TrendFollowerBot
from app.bots.metals_bot import MetalsBot
from app.bots.stock_analyzer import AIStockAnalyzerBot

BOT_CLASSES = [
    TrendFollowerBot,
    ForexScalperBot,
    SmartMoneyBot,
    BreakoutBot,
    NewsBot,
    DcaBot,
    TokenizationBot,
    AIStockAnalyzerBot,
    MetalsBot,
    CommoditiesBot,
]


def load_data(symbol: str) -> pd.DataFrame:
    raw = yf.download(
        symbol,
        start="2022-01-01",
        end="2025-01-16",
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
        timeout=15,
    )
    data = raw.xs(symbol, axis=1, level=1) if isinstance(raw.columns, pd.MultiIndex) else raw
    data.columns = [str(column).lower() for column in data.columns]
    return data.dropna(subset=["open", "high", "low", "close", "volume"])


def signal_value(signal: Any, *names: str) -> Optional[float]:
    for name in names:
        value = getattr(signal, name, None)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
    return None


def signal_side(signal: Any) -> Optional[str]:
    side = getattr(signal, "action", None) or getattr(signal, "side", None)
    if isinstance(side, str):
        side = side.upper()
        return {"LONG": "BUY", "SHORT": "SELL"}.get(side, side)
    return None


def outcome(signal: Any, future: pd.DataFrame) -> Optional[float]:
    side = signal_side(signal)
    entry = signal_value(signal, "entry_price", "entry")
    stop = signal_value(signal, "stop_loss")
    target = signal_value(signal, "take_profit")
    if side not in {"BUY", "SELL"} or entry is None or stop is None or target is None:
        return None
    if side == "BUY":
        stop_hit = future["low"].le(stop)
        target_hit = future["high"].ge(target)
        risk = entry - stop
        if risk <= 0:
            return None
        if stop_hit.any() and target_hit.any():
            return -1.0 if stop_hit.idxmax() <= target_hit.idxmax() else 2.0
        if stop_hit.any():
            return -1.0
        if target_hit.any():
            return 2.0
        return (future["close"].iloc[-1] - entry) / risk
    stop_hit = future["high"].ge(stop)
    target_hit = future["low"].le(target)
    risk = stop - entry
    if risk <= 0:
        return None
    if stop_hit.any() and target_hit.any():
        return -1.0 if stop_hit.idxmax() <= target_hit.idxmax() else 2.0
    if stop_hit.any():
        return -1.0
    if target_hit.any():
        return 2.0
    return (entry - future["close"].iloc[-1]) / risk


async def test_bot(bot_class: type[BaseBot], data: pd.DataFrame) -> Dict[str, Any]:
    bot = bot_class({"bot_id": f"real_{bot_class.__name__}", "parameters": {}})
    results = []
    signal_count = 0
    horizon = 10
    for index in range(60, len(data) - horizon):
        signal = await bot.analyze_market(data.iloc[: index + 1])
        if signal is None:
            continue
        signal_count += 1
        value = outcome(signal, data.iloc[index + 1 : index + 1 + horizon])
        if value is not None:
            results.append(value)
    wins = [value for value in results if value > 0]
    losses = [value for value in results if value <= 0]
    equity = pd.Series(results).cumsum() if results else pd.Series(dtype=float)
    drawdown = float((equity.cummax() - equity).max()) if not equity.empty else 0.0
    return {
        "status": "VALIDATED" if results else "NOT_VALIDATED_NO_TRADES",
        "signals": signal_count,
        "trades": len(results),
        "win_rate_pct": round(len(wins) / len(results) * 100, 2) if results else 0.0,
        "profit_factor": round(sum(wins) / abs(sum(losses)), 3) if losses else None,
        "expectancy_R": round(sum(results) / len(results), 4) if results else 0.0,
        "max_drawdown_R": round(drawdown, 4),
    }


async def run() -> None:
    reports: Dict[str, Any] = {}
    for symbol in ("SPY", "BTC-USD"):
        data = load_data(symbol)
        reports[symbol] = {
            "rows": len(data),
            "start": str(data.index[0].date()) if not data.empty else None,
            "end": str(data.index[-1].date()) if not data.empty else None,
            "bots": {},
        }
        for bot_class in BOT_CLASSES:
            try:
                reports[symbol]["bots"][bot_class.__name__] = await test_bot(bot_class, data)
            except Exception as error:
                reports[symbol]["bots"][bot_class.__name__] = {"error": str(error)}
            output = ROOT / "data" / "reports" / "real_bot_baseline.json"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(reports, indent=2), encoding="utf-8")
            print(f"completed={symbol}:{bot_class.__name__}", flush=True)
    output = ROOT / "data" / "reports" / "real_bot_baseline.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    asyncio.run(run())
