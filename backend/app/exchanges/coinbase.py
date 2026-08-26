from .base_exchange import BaseExchange

class CoinbaseExchange(BaseExchange):
    def __init__(self, api_key=None, secret_key=None, passphrase=None, **kwargs):
        super().__init__(api_key, secret_key, passphrase, **kwargs)

    async def get_ticker(self, symbol):
        return {'last': 0, 'bid': 0, 'ask': 0, 'volume': 0}

    async def fetch_ticker(self, symbol):
        return {'last': 0, 'bid': 0, 'ask': 0, 'volume': 0}

    async def create_market_buy_order(self, symbol, amount):
        return {'id': 'mock', 'filled': amount, 'price': 0}

    async def create_market_sell_order(self, symbol, amount):
        return {'id': 'mock', 'filled': amount, 'price': 0}

    async def create_limit_buy_order(self, symbol, amount, price):
        return {'id': 'mock', 'filled': 0, 'price': price}

    async def create_limit_sell_order(self, symbol, amount, price):
        return {'id': 'mock', 'filled': 0, 'price': price}

    async def create_stop_buy_order(self, symbol, amount, stopPrice):
        return {'id': 'mock'}

    async def create_stop_sell_order(self, symbol, amount, stopPrice):
        return {'id': 'mock'}

    async def create_stop_limit_buy_order(self, symbol, amount, stopPrice, price):
        return {'id': 'mock'}

    async def create_stop_limit_sell_order(self, symbol, amount, stopPrice, price):
        return {'id': 'mock'}

    async def cancel_order(self, order_id, symbol):
        return True

    def fetch_order_book(self, symbol):
        return {'bids': [], 'asks': []}
