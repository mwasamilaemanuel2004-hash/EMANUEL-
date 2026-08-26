# backend/app/exchanges/okx.py
"""
OKX EXCHANGE - ULTRA ADVANCED
"""

import hmac
import hashlib
import base64
import time
from typing import Dict, Optional
from datetime import datetime
from loguru import logger

from .base_exchange import BaseExchange, ExchangeConfig, Ticker, OrderBook, Balance, OrderResult

class OKXExchange(BaseExchange):
    """OKX Exchange Integration"""
    
    def __init__(self, config: ExchangeConfig):
        super().__init__(config)
        self.base_url = "https://www.okx.com/api/v5"
        self.passphrase = config.passphrase
        
        logger.info(f"📊 OKX initialized")
    
    async def ping(self) -> bool:
        try:
            response = await self._request('GET', '/market/tickers', {'instType': 'SPOT'})
            return 'data' in response
        except:
            return False
    
    async def get_ticker(self, symbol: str) -> Optional[Ticker]:
        try:
            response = await self._request('GET', '/market/ticker', {'instId': symbol})
            
            if 'error' in response:
                return None
            
            data = response.get('data', [])
            if not data:
                return None
            
            ticker_data = data[0]
            return Ticker(
                symbol=symbol,
                bid=float(ticker_data.get('bidPx', 0)),
                ask=float(ticker_data.get('askPx', 0)),
                last=float(ticker_data.get('last', 0)),
                high=float(ticker_data.get('high24h', 0)),
                low=float(ticker_data.get('low24h', 0)),
                volume=float(ticker_data.get('vol24h', 0)),
                change=float(ticker_data.get('last', 0)) - float(ticker_data.get('open24h', 0)),
                change_percent=(float(ticker_data.get('last', 0)) / float(ticker_data.get('open24h', 1)) - 1) * 100
            )
        except Exception as e:
            logger.error(f"OKX get_ticker error: {e}")
            return None
    
    async def get_order_book(self, symbol: str, limit: int = 10) -> Optional[OrderBook]:
        try:
            response = await self._request('GET', '/market/books', {'instId': symbol, 'sz': limit})
            
            if 'error' in response:
                return None
            
            data = response.get('data', [])
            if not data:
                return None
            
            order_data = data[0]
            bids = [(float(b[0]), float(b[1])) for b in order_data.get('bids', [])[:limit]]
            asks = [(float(a[0]), float(a[1])) for a in order_data.get('asks', [])[:limit]]
            
            return OrderBook(symbol=symbol, bids=bids, asks=asks)
        except Exception as e:
            logger.error(f"OKX get_order_book error: {e}")
            return None
    
    async def get_balance(self, asset: str) -> Optional[Balance]:
        try:
            response = await self._signed_request('GET', '/account/balance', {'ccy': asset})
            
            if 'error' in response:
                return None
            
            data = response.get('data', [])
            if not data:
                return None
            
            balance_data = data[0]
            details = balance_data.get('details', [])
            for detail in details:
                if detail['ccy'] == asset:
                    total = float(detail.get('eq', 0))
                    available = float(detail.get('availEq', 0))
                    return Balance(asset=asset, free=available, used=total - available, total=total)
            
            return Balance(asset=asset, free=0, used=0, total=0)
        except Exception as e:
            logger.error(f"OKX get_balance error: {e}")
            return None
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = 'market',
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Optional[OrderResult]:
        try:
            params = {
                'instId': symbol,
                'side': side.upper(),
                'ordType': order_type.upper(),
                'sz': str(quantity)
            }
            
            if order_type.lower() == 'limit' and price:
                params['px'] = str(price)
            
            if order_type.lower() == 'stop' and stop_price:
                params['stopPx'] = str(stop_price)
                params['stopOrdType'] = 'move'
            
            response = await self._signed_request('POST', '/trade/order', params)
            
            if 'error' in response:
                return None
            
            data = response.get('data', [])
            if not data:
                return None
            
            order_data = data[0]
            return OrderResult(
                order_id=order_data.get('ordId', ''),
                symbol=symbol,
                side=side.lower(),
                order_type=order_type.lower(),
                price=float(order_data.get('px', 0)),
                quantity=float(order_data.get('sz', 0)),
                filled_quantity=float(order_data.get('accFillSz', 0)),
                filled_price=float(order_data.get('avgPx', 0)),
                status=order_data.get('state', 'PENDING')
            )
        except Exception as e:
            logger.error(f"OKX place_order error: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        try:
            response = await self._signed_request('POST', '/trade/cancel-order', {'ordId': order_id})
            return 'error' not in response
        except Exception as e:
            logger.error(f"OKX cancel_order error: {e}")
            return False
    
    async def get_order_status(self, order_id: str) -> Dict:
        try:
            response = await self._signed_request('GET', '/trade/order', {'ordId': order_id})
            data = response.get('data', [])
            return data[0] if data else {'status': 'ERROR'}
        except Exception as e:
            logger.error(f"OKX get_order_status error: {e}")
            return {'status': 'ERROR'}
    
    async def _signed_request(self, method: str, endpoint: str, params: Dict = None) -> Dict:
        timestamp = str(int(time.time()))
        
        if params is None:
            params = {}
        
        method_upper = method.upper()
        
        signature_string = timestamp + method_upper + endpoint
        if method_upper == 'GET' and params:
            signature_string += '?' + '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        elif method_upper == 'POST':
            import json
            signature_string += json.dumps(params)
        
        signature = base64.b64encode(
            hmac.new(
                self.config.secret_key.encode('utf-8'),
                signature_string.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        headers = {
            'OK-ACCESS-KEY': self.config.api_key,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-PASSPHRASE': self.passphrase
        }
        
        return await self._request(method, endpoint, params=params, headers=headers)