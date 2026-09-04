import sys

sys.path.insert(0, "backend")
from app.bots.base_bot import UltraAdvancedBaseBot


def test_long_side_and_drawdown() -> None:
    bot = UltraAdvancedBaseBot("test", "BTCUSDT", 1000.0)
    position = bot.open_position("long", 100.0, 0.8, 1.0)
    assert position is not None
    assert position.side == "BUY"
    closed = bot.close_position(position.id, 90.0, "test")
    assert closed is not None
    metrics = bot.get_performance_metrics()
    assert metrics["losing_trades"] == 1
    assert metrics["max_drawdown"] > 0


if __name__ == "__main__":
    test_long_side_and_drawdown()
    print("ultra_advanced=ok")
