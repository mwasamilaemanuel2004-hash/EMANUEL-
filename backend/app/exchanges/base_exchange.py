class BaseExchange:
    def __init__(self, api_key=None, secret_key=None, passphrase=None, **kwargs):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    async def get_ticker(self, symbol):
        raise NotImplementedError

    async def fetch_ticker(self, symbol):
        raise NotImplementedError

    async def create_market_buy_order(self, symbol, amount):
        raise NotImplementedError

    async def create_market_sell_order(self, symbol, amount):
        raise NotImplementedError

    async def create_limit_buy_order(self, symbol, amount, price):
        raise NotImplementedError

    async def create_limit_sell_order(self, symbol, amount, price):
        raise NotImplementedError

    async def create_stop_buy_order(self, symbol, amount, stopPrice):
        raise NotImplementedError

    async def create_stop_sell_order(self, symbol, amount, stopPrice):
        raise NotImplementedError

    async def create_stop_limit_buy_order(self, symbol, amount, stopPrice, price):
        raise NotImplementedError

    async def create_stop_limit_sell_order(self, symbol, amount, stopPrice, price):
        raise NotImplementedError

    async def cancel_order(self, order_id, symbol):
        raise NotImplementedError

    def fetch_order_book(self, symbol):
        raise NotImplementedError
