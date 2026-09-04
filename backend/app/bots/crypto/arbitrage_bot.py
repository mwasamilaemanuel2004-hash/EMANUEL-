"""Cross-exchange arbitrage bot.

The bot requires exchange quotes in the input mapping. OHLCV candles alone do
not contain enough information to identify an arbitrage opportunity.
"""
from typing import Any, Dict, Optional

from ..base_bot import BaseBot, TradeSignal, SignalStrength, TradeQuality


class ArbitrageBot(BaseBot):
	"""Generate a signal when two exchange quotes exceed the configured edge."""

	def __init__(self, config: Dict[str, Any]):
		super().__init__("Arbitrage", config)
		self.min_edge_pct = float(config.get("min_edge_pct", 0.2))

	async def analyze_market(self, data: Any) -> Optional[TradeSignal]:
		if not isinstance(data, dict):
			return None

		quotes = data.get("quotes")
		if not isinstance(quotes, dict) or len(quotes) < 2:
			return None

		valid_quotes = {
			exchange: float(price)
			for exchange, price in quotes.items()
			if isinstance(price, (int, float)) and price > 0
		}
		if len(valid_quotes) < 2:
			return None

		buy_exchange = min(valid_quotes, key=valid_quotes.get)
		sell_exchange = max(valid_quotes, key=valid_quotes.get)
		buy_price = valid_quotes[buy_exchange]
		sell_price = valid_quotes[sell_exchange]
		edge_pct = (sell_price - buy_price) / buy_price * 100
		if edge_pct < self.min_edge_pct:
			return None

		return TradeSignal(
			action="BUY",
			confidence=min(99.0, 70.0 + edge_pct * 10),
			strength=SignalStrength.STRONG,
			quality=TradeQuality.GOOD,
			entry_price=buy_price,
			stop_loss=buy_price,
			take_profit=sell_price,
			position_size=0.0,
			reason=f"Buy on {buy_exchange}, sell on {sell_exchange}",
			supporting_indicators=["cross_exchange_spread"],
			ai_reasoning="Validated quote spread before fees and transfer costs.",
			risk_score=0.0,
			expected_return=edge_pct,
			time_horizon="immediate",
			metadata={
				"buy_exchange": buy_exchange,
				"sell_exchange": sell_exchange,
				"edge_pct": edge_pct,
			},
		)
