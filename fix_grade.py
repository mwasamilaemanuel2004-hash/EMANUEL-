p = 'backend/app/core/ai_overseer/__init__.py'
s = open(p).read()

old = '''class TradeGrade:
    NO_TRADE = (0, 59, "NO_TRADE")
    WATCH = (60, 69, "WATCH")
    NORMAL = (70, 79, "NORMAL_ENTRY")
    HIGH_CONFIDENCE = (80, 89, "HIGH_CONFIDENCE")
    PREMIUM = (90, 100, "PREMIUM_SNIPER")

    def __init__(self, min_score, max_score, label):
        self.min_score = min_score
        self.max_score = max_score
        self.label = label

    @classmethod
    def from_score(cls, score: float) -> 'TradeGrade':
        for grade in [cls.PREMIUM, cls.HIGH_CONFIDENCE, cls.NORMAL, cls.WATCH, cls.NO_TRADE]:
            if grade.min_score <= score <= grade.max_score:
                return grade
        return cls.NO_TRADE'''

new = '''class _Grade:
    def __init__(self, mn, mx, lbl):
        self.min_score = mn
        self.max_score = mx
        self.label = lbl


class TradeGrade:
    NO_TRADE = _Grade(0, 59, "NO_TRADE")
    WATCH = _Grade(60, 69, "WATCH")
    NORMAL = _Grade(70, 79, "NORMAL_ENTRY")
    HIGH_CONFIDENCE = _Grade(80, 89, "HIGH_CONFIDENCE")
    PREMIUM = _Grade(90, 100, "PREMIUM_SNIPER")

    @classmethod
    def from_score(cls, score: float):
        for g in [cls.PREMIUM, cls.HIGH_CONFIDENCE, cls.NORMAL, cls.WATCH, cls.NO_TRADE]:
            if g.min_score <= score <= g.max_score:
                return g
        return cls.NO_TRADE'''

assert old in s, "old TradeGrade block not found"
s = s.replace(old, new)
open(p, 'w').write(s)
print("TradeGrade fixed:", s.count("_Grade(0, 59"))
