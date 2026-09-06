"""Unified execution gateway for exchange and broker adapters.

The gateway keeps strategy code independent from provider-specific APIs. CCXT
covers supported crypto exchanges; MT5, Deriv, and stock brokers can implement
BrokerAdapter without changing any bot. Live orders remain opt-in.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol


@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    side: str
    order_type: str = "market"
    amount: float = 0.0
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    client_order_id: Optional[str] = None


@dataclass(frozen=True)
class OrderResult:
    provider: str
    order_id: str
    symbol: str
    side: str
    amount: float
    price: Optional[float]
    status: str
    dry_run: bool
    raw: Dict[str, Any] = field(default_factory=dict)


class BrokerAdapter(Protocol):
    provider: str

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]: ...

    async def create_order(self, request: OrderRequest) -> OrderResult: ...

    async def cancel_order(self, order_id: str, symbol: str) -> bool: ...


class GatewayError(RuntimeError):
    """Raised when an order cannot pass gateway validation or execution."""


class ExecutionGateway:
    """Risk-aware provider gateway shared by all market bots."""

    def __init__(self, adapter: BrokerAdapter, *, live_trading: bool = False,
                 max_order_value: float = 0.0) -> None:
        self.adapter = adapter
        self.live_trading = live_trading
        self.max_order_value = max(0.0, float(max_order_value))

    async def ticker(self, symbol: str) -> Dict[str, Any]:
        return await self.adapter.fetch_ticker(self.normalize_symbol(symbol))

    async def submit(self, request: OrderRequest) -> OrderResult:
        request = self.validate(request)
        if not self.live_trading:
            return OrderResult(
                provider=self.adapter.provider,
                order_id=f"dry-run-{request.client_order_id or request.symbol}",
                symbol=request.symbol,
                side=request.side,
                amount=request.amount,
                price=request.price,
                status="dry_run",
                dry_run=True,
            )
        return await self.adapter.create_order(request)

    def validate(self, request: OrderRequest) -> OrderRequest:
        symbol = self.normalize_symbol(request.symbol)
        side = request.side.lower()
        order_type = request.order_type.lower()
        if not symbol or side not in {"buy", "sell"}:
            raise GatewayError("symbol and side must be valid")
        if order_type not in {"market", "limit", "stop"}:
            raise GatewayError("unsupported order type")
        if request.amount <= 0:
            raise GatewayError("order amount must be positive")
        if order_type == "limit" and (request.price is None or request.price <= 0):
            raise GatewayError("limit orders require a positive price")
        if self.max_order_value and request.price:
            if request.amount * request.price > self.max_order_value:
                raise GatewayError("order exceeds gateway notional limit")
        return OrderRequest(
            symbol=symbol, side=side, order_type=order_type,
            amount=float(request.amount), price=request.price,
            stop_loss=request.stop_loss, take_profit=request.take_profit,
            client_order_id=request.client_order_id,
        )

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        return str(symbol or "").strip().upper().replace("-", "/")


class CCXTAdapter:
    """Adapter for CCXT-supported crypto exchanges.

    Import is lazy so the backend can still run with broker-only deployments.
    """

    def __init__(self, exchange_id: str, credentials: Optional[Dict[str, Any]] = None,
                 *, sandbox: bool = True) -> None:
        try:
            import ccxt.async_support as ccxt  # type: ignore
        except ImportError as exc:
            raise GatewayError("ccxt is required for CCXT providers") from exc
        exchange_type = getattr(ccxt, exchange_id, None)
        if exchange_type is None:
            raise GatewayError(f"unsupported CCXT provider: {exchange_id}")
        config = dict(credentials or {})
        config.setdefault("enableRateLimit", True)
        self.client = exchange_type(config)
        self.provider = exchange_id
        if sandbox and hasattr(self.client, "set_sandbox_mode"):
            self.client.set_sandbox_mode(True)

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        return await self.client.fetch_ticker(symbol)

    async def create_order(self, request: OrderRequest) -> OrderResult:
        raw = await self.client.create_order(
            request.symbol, request.order_type, request.side,
            request.amount, request.price,
            {"stopLossPrice": request.stop_loss,
             "takeProfitPrice": request.take_profit},
        )
        return OrderResult(
            provider=self.provider, order_id=str(raw.get("id", "")),
            symbol=request.symbol, side=request.side, amount=request.amount,
            price=raw.get("average") or raw.get("price"),
            status=str(raw.get("status", "submitted")), dry_run=False,
            raw=raw,
        )

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        await self.client.cancel_order(order_id, symbol)
        return True


async def close_adapter(adapter: BrokerAdapter) -> None:
    client = getattr(adapter, "client", None)
    close = getattr(client, "close", None)
    if close is not None:
        await close()
