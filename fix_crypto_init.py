p = 'backend/app/bots/crypto/__init__.py'
s = open(p).read()
old = (
    'from .arbitrage_bot import ArbitrageBot\n'
    'from .scalper_bot import CryptoScalperBot\n'
    'from .dca_bot import DcaBot\n'
    'from .grib_bot import GridBot\n'
    'from .whale_bot import WhaleBot\n'
    '\n'
    '__all__ = [\n'
    '    "ArbitrageBot",\n'
    '    "CryptoScalperBot",\n'
    '    "DcaBot",\n'
    '    "GridBot",\n'
    '    "WhaleBot",\n'
    ']'
)
new = (
    'from .arbitrage_bot import ArbitrageBot\n'
    'from .scalper_bot import CryptoScalperBot\n'
    'from .dca_bot import DcaBot\n'
    'from .grib_bot import GridBot\n'
    'from .whale_bot import WhaleBot\n'
    'from .tokenization_bot import TokenizationBot\n'
    '\n'
    '__all__ = [\n'
    '    "ArbitrageBot",\n'
    '    "CryptoScalperBot",\n'
    '    "DcaBot",\n'
    '    "GridBot",\n'
    '    "WhaleBot",\n'
    '    "TokenizationBot",\n'
    ']'
)
assert old in s, 'old block not found'
s = s.replace(old, new)
open(p, 'w').write(s)
print('crypto __init__ updated, TokenizationBot added')
