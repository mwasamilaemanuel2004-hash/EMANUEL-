import asyncio
import sys

sys.path.insert(0, "backend")

from app.execution.universal_gateway import (  # noqa: E402
    ExecutionGateway,
    GatewayError,
    OrderRequest,
)


class FakeAdapter:
    provider = "fake"

    async def fetch_ticker(self, symbol):
        return {"symbol": symbol, "last": 100.0}

    async def create_order(self, request):
        raise AssertionError("dry-run must not call the adapter")

    async def cancel_order(self, order_id, symbol):
        return True


def main() -> None:
    gateway = ExecutionGateway(FakeAdapter(), max_order_value=1000)
    result = asyncio.run(gateway.submit(OrderRequest("btc-usdt", "BUY", amount=0.05, price=100)))
    assert result.dry_run is True
    assert result.status == "dry_run"
    assert result.symbol == "BTC/USDT"
    assert result.asset_class == "crypto"

    assert gateway.classify_symbol("EURUSD") == "forex"
    assert gateway.classify_symbol("XAUUSD") == "metals"
    assert gateway.classify_symbol("R_75") == "deriv"
    assert gateway.classify_symbol("AAPL") == "stocks"
    custom_coin = gateway.validate(
        OrderRequest("NEWCOIN", "buy", amount=5, price=1, asset_class="crypto")
    )
    assert custom_coin.asset_class == "crypto"

    market_result = asyncio.run(
        gateway.submit(OrderRequest("EURUSD", "buy", amount=0.1))
    )
    assert market_result.status == "dry_run"

    try:
        asyncio.run(gateway.submit(OrderRequest("BTC/USDT", "buy", amount=20, price=100)))
    except GatewayError:
        pass
    else:
        raise AssertionError("notional limit must reject oversized orders")

    try:
        asyncio.run(gateway.submit(OrderRequest("BTC/USDT", "buy", amount=0.01)))
    except GatewayError:
        pass
    else:
        raise AssertionError("market notional below $5 must be rejected")

    print("universal_gateway=ok")


if __name__ == "__main__":
    main()
