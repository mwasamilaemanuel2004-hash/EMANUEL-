"""Deterministic, signal-based Deriv backtesting for historical price series."""

from typing import Any

from .service import DerivBotService, DerivRequest


def run_deriv_backtest(
    request: DerivRequest,
    prices: list[float],
    initial_balance: float | None = None,
) -> dict[str, Any]:
    if len(prices) < 21:
        raise ValueError("At least 21 positive prices are required for a backtest")
    if any(price <= 0 for price in prices):
        raise ValueError("Prices must be positive")

    balance = initial_balance or request.balance
    service = DerivBotService()
    trades: list[dict[str, Any]] = []
    losses = 0
    daily_loss = 0.0
    peak = balance
    max_drawdown = 0.0

    for index in range(20, len(prices) - 1):
        drawdown = (peak - balance) / peak if peak else 0
        plan = service.plan(request, prices[index - 20:index + 1], daily_loss=daily_loss, losses=losses, equity=balance, drawdown=drawdown)
        if not plan["risk"]["allowed"]:
            continue
        signal = plan["analysis"]["signal"]
        next_price = prices[index + 1]
        won = (signal == "BUY" and next_price > prices[index]) or (
            signal == "SELL" and next_price < prices[index]
        )
        stake = plan["risk"]["stake"]
        pnl = round(stake * (0.8 if won else -1), 2)
        balance = round(balance + pnl, 2)
        daily_loss = max(0.0, daily_loss - pnl) if pnl < 0 else max(0.0, daily_loss - pnl)
        losses = 0 if won else losses + 1
        peak = max(peak, balance)
        max_drawdown = max(max_drawdown, peak - balance)
        trades.append({
            "index": index,
            "signal": signal,
            "entry_price": prices[index],
            "exit_price": next_price,
            "stake": stake,
            "pnl": pnl,
            "won": won,
        })

    wins = sum(1 for trade in trades if trade["won"])
    gross_profit = sum(trade["pnl"] for trade in trades if trade["pnl"] > 0)
    gross_loss = abs(sum(trade["pnl"] for trade in trades if trade["pnl"] < 0))
    average_pnl = sum(trade["pnl"] for trade in trades) / len(trades) if trades else 0
    losing_streak = winning_streak = current_losses = current_wins = 0
    for trade in trades:
        current_losses = current_losses + 1 if not trade["won"] else 0
        current_wins = current_wins + 1 if trade["won"] else 0
        losing_streak = max(losing_streak, current_losses)
        winning_streak = max(winning_streak, current_wins)
    return {
        "symbol": request.symbol,
        "strategy": request.strategy.value if request.strategy else "ai_adaptive",
        "initial_balance": initial_balance or request.balance,
        "final_balance": balance,
        "total_trades": len(trades),
        "wins": wins,
        "losses": len(trades) - wins,
        "win_rate": round((wins / len(trades)) * 100, 2) if trades else 0.0,
        "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss else None,
        "max_drawdown": round(max_drawdown, 2),
        "max_drawdown_percent": round((max_drawdown / peak) * 100, 2) if peak else 0,
        "roi": round(((balance / (initial_balance or request.balance)) - 1) * 100, 2),
        "expectancy": round(average_pnl, 4),
        "average_win": round(gross_profit / wins, 4) if wins else 0,
        "average_loss": round(gross_loss / (len(trades) - wins), 4) if len(trades) > wins else 0,
        "losing_streak": losing_streak,
        "winning_streak": winning_streak,
        "risk_of_ruin_estimate": round(min(1.0, (losing_streak / max(len(trades), 1)) * (max_drawdown / max(peak, 1))), 4),
        "trades": trades,
    }