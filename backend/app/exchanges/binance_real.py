"""
Binance Real Market Data Integration
Live and historical data from Binance exchange
"""

import hmac
import hashlib
import time
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
import httpx
import pandas as pd
import numpy as np


class BinanceConfig:
    """Binance API Configuration"""
    BASE_URL = "https://api.binance.com"
    TESTNET_URL = "https://testnet.binance.vision"
    FAPI_URL = "https://fapi.binance.com"
    DAPI_URL = "https://dapi.binance.com"
    REQUEST_WEIGHT_LIMIT = 1200
    ORDERS_LIMIT = 100


class BinanceRealExchange:
    """Real Binance Exchange Integration - Spot, Futures, Margin"""
    
    def __init__(self, api_key: str = None, secret_key: str = None, testnet: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        self.base_url = BinanceConfig.TESTNET_URL if testnet else BinanceConfig.BASE_URL
        self.fapi_url = BinanceConfig.FAPI_URL
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-MBX-APIKEY": api_key or "", "Content-Type": "application/json"},
            timeout=30.0
        )
        self._request_count = 0
        self._last_reset = time.time()
        logger.info(f"Binance Exchange initialized (testnet={testnet})")
    
    def _generate_signature(self, query_string: str) -> str:
        return hmac.new(
            self.secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256
        ).hexdigest()
    
    def _get_timestamp(self) -> int:
        return int(time.time() * 1000)
    
    async def _check_rate_limit(self):
        current_time = time.time()
        if current_time - self._last_reset >= 60:
            self._request_count = 0
            self._last_reset = current_time
        if self._request_count >= BinanceConfig.REQUEST_WEIGHT_LIMIT * 0.8:
            wait_time = 60 - (current_time - self._last_reset)
            if wait_time > 0:
                logger.warning(f"Rate limit approaching, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                self._request_count = 0
                self._last_reset = time.time()
        self._request_count += 1

    # ============================================
    # MARKET DATA ENDPOINTS
    # ============================================
    
    async def test_connectivity(self) -> Dict:
        try:
            response = await self.client.get("/api/v3/ping")
            return {"status": "ok" if response.status_code == 200 else "error", "latency": response.elapsed.total_seconds()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def get_server_time(self) -> Dict:
        response = await self.client.get("/api/v3/time")
        return response.json()
    
    async def get_exchange_info(self) -> Dict:
        response = await self.client.get("/api/v3/exchangeInfo")
        return response.json()
    
    async def get_ticker(self, symbol: str) -> Dict:
        await self._check_rate_limit()
        response = await self.client.get("/api/v3/ticker/24hr", params={"symbol": symbol})
        data = response.json()
        return {
            "symbol": data.get("symbol"),
            "last_price": float(data.get("lastPrice", 0)),
            "bid_price": float(data.get("bidPrice", 0)),
            "ask_price": float(data.get("askPrice", 0)),
            "volume": float(data.get("volume", 0)),
            "quote_volume": float(data.get("quoteVolume", 0)),
            "high_price": float(data.get("highPrice", 0)),
            "low_price": float(data.get("lowPrice", 0)),
            "price_change": float(data.get("priceChange", 0)),
            "price_change_percent": float(data.get("priceChangePercent", 0)),
            "weighted_avg_price": float(data.get("weightedAvgPrice", 0)),
            "open_price": float(data.get("openPrice", 0)),
            "prev_close": float(data.get("prevClosePrice", 0)),
            "trades_count": int(data.get("count", 0)),
            "timestamp": data.get("closeTime")
        }
    
    async def get_all_tickers(self) -> List[Dict]:
        await self._check_rate_limit()
        response = await self.client.get("/api/v3/ticker/24hr")
        tickers = response.json()
        return [{
            "symbol": t["symbol"], "last_price": float(t["lastPrice"]),
            "volume": float(t["volume"]), "price_change_percent": float(t["priceChangePercent"]),
            "quote_volume": float(t["quoteVolume"])
        } for t in tickers]
    
    async def get_orderbook(self, symbol: str, limit: int = 100) -> Dict:
        await self._check_rate_limit()
        response = await self.client.get("/api/v3/depth", params={"symbol": symbol, "limit": limit})
        data = response.json()
        return {
            "symbol": symbol,
            "bids": [[float(p), float(q)] for p, q in data.get("bids", [])],
            "asks": [[float(p), float(q)] for p, q in data.get("asks", [])],
            "last_update_id": data.get("lastUpdateId")
        }

    async def get_klines(self, symbol: str, interval: str = "1h", limit: int = 500,
                         start_time: int = None, end_time: int = None) -> pd.DataFrame:
        await self._check_rate_limit()
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        response = await self.client.get("/api/v3/klines", params=params)
        data = response.json()
        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades_count", "taker_buy_base",
            "taker_buy_quote", "ignore"
        ])
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
        numeric_cols = ["open", "high", "low", "close", "volume", "quote_volume", "taker_buy_base", "taker_buy_quote"]
        df[numeric_cols] = df[numeric_cols].astype(float)
        df["trades_count"] = df["trades_count"].astype(int)
        return df

    async def get_recent_trades(self, symbol: str, limit: int = 500) -> List[Dict]:
        await self._check_rate_limit()
        response = await self.client.get("/api/v3/trades", params={"symbol": symbol, "limit": limit})
        trades = response.json()
        return [{
            "id": t["id"], "price": float(t["price"]), "qty": float(t["qty"]),
            "quote_qty": float(t["quoteQty"]), "time": t["time"], "is_buyer_maker": t["isBuyerMaker"]
        } for t in trades]

    async def get_agg_trades(self, symbol: str, limit: int = 500,
                             start_time: int = None, end_time: int = None) -> List[Dict]:
        await self._check_rate_limit()
        params = {"symbol": symbol, "limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        response = await self.client.get("/api/v3/aggTrades", params=params)
        trades = response.json()
        return [{
            "agg_trade_id": t["a"], "price": float(t["p"]), "qty": float(t["q"]),
            "first_trade_id": t["f"], "last_trade_id": t["l"], "timestamp": t["T"], "is_buyer_maker": t["m"]
        } for t in trades]