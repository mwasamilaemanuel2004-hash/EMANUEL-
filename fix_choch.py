p = 'backend/app/core/sm_engine.py'
s = open(p).read()
old = '''def _choch_confirmed(df: pd.DataFrame, eb: int, side: str) -> bool:
    """
    CHoCH: the confirmation candle (entry bar) closes beyond the prior
    LTF swing in the trade direction.
    For BUY: close > max(high[eb-10:eb])  (break of prior swing high)
    For SELL: close < min(low[eb-10:eb])   (break of prior swing low)
    """
    if eb < 10:
        return False
    closes = df['close']; highs = df['high']; lows = df['low']
    c = float(closes.iloc[eb])
    if side == 'BUY':
        # Need to break above the prior swing high
        prior_sh = float(highs.iloc[max(0, eb-10):eb].max())
        return c > prior_sh
    else:
        prior_sl = float(lows.iloc[max(0, eb-10):eb].min())
        return c < prior_sl'''
new = '''def _choch_confirmed(df: pd.DataFrame, eb: int, side: str) -> bool:
    """
    CHoCH: the confirmation candle closes beyond the recent local swing.
    For BUY: close[eb] > max(high[eb-3:eb])  (breaks the 3-bar swing high)
    For SELL: close[eb] < min(low[eb-3:eb])   (breaks the 3-bar swing low)
    """
    if eb < 3:
        return False
    closes = df['close']; highs = df['high']; lows = df['low']
    c = float(closes.iloc[eb])
    if side == 'BUY':
        return c > float(highs.iloc[eb-3:eb].max())
    else:
        return c < float(lows.iloc[eb-3:eb].min())'''
assert old in s, 'choch block not found'
s = s.replace(old, new)
open(p, 'w').write(s)
print('CHoCH relaxed to 3-bar:', 'eb-3:eb' in s)
