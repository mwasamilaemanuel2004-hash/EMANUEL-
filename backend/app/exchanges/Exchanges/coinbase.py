# backend/app/exchanges/coinbase.py
"""
COINBASE EXCHANGE - ULTRA ADVANCED
"""

import hmac
import hashlib
import base64
import time
from typing import Dict, Optional
from datetime import datetime
from loguru import logger

from .base_exchange import BaseExchange, ExchangeConfig, Ticker, OrderBook, Balance, OrderResult

class CoinbaseExchange(BaseExchange):
    """Coinbase Exchange Integration"""
    
    def __init__(self, config: ExchangeConfig):
        super().__init__(config)
        self.base_url = "https://api.coinbase.com/api/v3/brokerage"
        self.passphrase = config.passphrase
        
        logger.info(f"📊 Coinbase initialized")
    
    async def ping(self) -> bool:
        try:
            response = await self._request('GET', '/products')
            return isinstance(response, list) or 'products' in response
        except:
            return False
    
    async def get_ticker(self, symbol: str) -> Optional[Ticker]:
        try:
            response = await self._request('GET', f'/products/{symbol}')
            
            if 'error' in response:
                return None
            
            return Ticker(
                symbol=symbol,
                bid=float(response.get('bid', 0)),
                ask=float(response.get('ask', 0)),
                last=float(response.get('price', 0)),
                high=0,
                low=0,
                volume=float(response.get('volume', 0)),
                change=0,
                change_percent=0
            )
        except Exception as e:
            logger.error(f"Coinbase get_ticker error: {e}")
            return None
    
    async def get_order_book(self, symbol: str, limit: int = 10) -> Optional[OrderBook]:
        try:
            response = await self._request('GET', f'/products/{symbol}/book', {'limit': limit})
            
            if 'error' in response:
                return None
            
            data = response.get('data', {})
            bids = [(float(b[0]), float(b[1])) for b in data.get('bids', [])[:limit]]
            asks = [(float(a[0]), float(a[1])) for a in data.get('asks', [])[:limit]]
            
            return OrderBook(symbol=symbol, bids=bids, asks=asks)
        except Exception as e:
            logger.error(f"Coinbase get_order_book error: {e}")
            return None
    
    async def get_balance(self, asset: str) -> Optional[Balance]:
        try:
            response = await self._signed_request('GET', '/accounts')
            
            if 'error' in response:
                return None
            
            data = response.get('data', [])
            for account in data:
                if account['currency'] == asset:
                    total = float(account.get('balance', 0))
                    available = float(account.get('available', 0))
                    return Balance(asset=asset, free=available, used=total - available, total=total)
            
            return Balance(asset=asset, free=0, used=0, total=0)
        except Exception as e:
            logger.error(f"Coinbase get_balance error: {e}")
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
                'product_id': symbol,
                'side': side.upper(),
                'order_type': order_type.upper()
            }
            
            if order_type.lower() == 'limit':
                params['limit_price'] = str(price)
                params['size'] = str(quantity)
            else:
                params['size'] = str(quantity)
            
            if order_type.lower() == 'stop' and stop_price:
                params['stop_price'] = str(stop_price)
                params['stop_direction'] = 'DOWN' if side.upper() == 'BUY' else 'UP'
            
            response = await self._signed_request('POST', '/orders', params)
            
            if 'error' in response:
                return None
            
            data = response.get('data', {})
            return OrderResult(
                order_id=data.get('order_id', ''),
                symbol=symbol,
                side=side.lower(),
                order_type=order_type.lower(),
                price=float(data.get('price', 0)),
                quantity=float(data.get('size', 0)),
                filled_quantity=float(data.get('filled_size', 0)),
                filled_price=float(data.get('price', 0)),
                status=data.get('status', 'PENDING')
            )
        except Exception as e:
            logger.error(f"Coinbase place_order error: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        try:
            response = await self._signed_request('DELETE', f'/orders/{order_id}')
            return 'error' not in response
        except Exception as e:
            logger.error(f"Coinbase cancel_order error: {e}")
            return False
    
    async def get_order_status(self, order_id: str) -> Dict:
        try:
            response = await self._signed_request('GET', f'/orders/{order_id}')
            return response.get('data', {}) if 'error' not in response else {'status': 'ERROR'}
        except Exception as e:
            logger.error(f"Coinbase get_order_status error: {e}")
            return {'status': 'ERROR'}
    
    async def _signed_request(self, method: str, endpoint: str, params: Dict = None) -> Dict:
        timestamp = str(int(time.time()))
        method_upper = method.upper()
        
        if params is None:
            params = {}
        
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
            'CB-ACCESS-KEY': self.config.api_key,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-SIGN': signature,
            'CB-ACCESS-PASSPHRASE': self.passphrase
        }
        
        return await self._request(method, endpoint, params=params, headers=headers)