p = 'backend/app/bots/__init__.py'
s = open(p).read()
old = (
    'from .crypto.whale_bot import WhaleBot\n'
    'from .stock_analyzer import AIStockAnalyzerBot'
)
new = (
    'from .crypto.whale_bot import WhaleBot\n'
    'from .crypto.tokenization_bot import TokenizationBot\n'
    'from .stock_analyzer import AIStockAnalyzerBot'
)
assert old in s, 'old not found'
s = s.replace(old, new)
# Update __all__
s = s.replace(
    '    "WhaleBot",\n    "AIStockAnalyzerBot", "MetalsBot", "CommoditiesBot",',
    '    "WhaleBot", "TokenizationBot",\n    "AIStockAnalyzerBot", "MetalsBot", "CommoditiesBot",'
)
open(p, 'w').write(s)
print('bots __init__ updated:', 'TokenizationBot' in s)
