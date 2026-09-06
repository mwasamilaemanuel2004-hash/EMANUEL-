"""Contract checks for scalper timeframe and risk configuration."""
import sys

sys.path.insert(0, "backend")

from app.bots.forex.forex_scapler import ForexScalperBot
from app.bots.crypto.scalper_bot import (
    CryptoScalperBot,
    MarketMicrostructure,
    MicrostructureAnalysis,
    TradeSide,
)


def main() -> None:
    forex = ForexScalperBot({"timeframe": "5m", "risk_per_trade_pct": 0.8})
    assert forex.timeframe == "5m"
    assert forex.risk_per_trade_pct == 0.8

    crypto = CryptoScalperBot({"timeframe": "15m", "risk_per_trade_pct": 1.0,
                               "start_background_tasks": False})
    assert crypto.timeframe == "15m"
    assert crypto.scalper_config.supported_timeframes == ("1m", "5m", "10m", "15m")
    assert crypto.scalper_config.risk_per_scalp == 0.01
    crypto.stop_scalping()

    maximum_risk = CryptoScalperBot({"timeframe": "1m", "risk_per_trade_pct": 5.0,
                                     "start_background_tasks": False})
    assert maximum_risk.scalper_config.risk_per_scalp == 0.05
    maximum_risk.stop_scalping()

    market = MicrostructureAnalysis(
        state=MarketMicrostructure.HIGH_LIQUIDITY,
        imbalance=0.0,
        spread=0.0002,
        liquidity=1000.0,
        volume_ratio=1.0,
        tick_velocity=0.0,
        volume_spike=False,
    )
    sized = crypto._calculate_position_size(TradeSide.BUY, 50000.0, 49850.0, market)
    assert 0 < sized <= crypto.capital * crypto.scalper_config.risk_per_scalp / 150.0
    assert crypto.scalper_config.min_position_size == 0.0

    print("scalper_config=ok")


if __name__ == "__main__":
    main()
