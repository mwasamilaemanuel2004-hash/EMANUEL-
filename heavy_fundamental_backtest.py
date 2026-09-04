"""
Heavy Fundamental Backtest — Full system validation across seeds and tokens.
Tests: Economic Quality, Token Capture, Dilution/Downside, Valuation/Upside
Execution: SmartEntryEngine (mandatory SL, breakeven@1R, unlimited runner)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

from app.core.token_analyzer import (
    TokenMetrics, RegulatoryStatus, NetworkPhase,
    compute_enhanced_token_score, estimate_timing_quality,
)
from app.core.token_fundamentals import compute_economic_quality, MacroData
from app.core.smart_entry import SmartEntryEngine

# TOKEN UNIVERSE
TOKENS: Dict[str, TokenMetrics] = {
    "BTC": TokenMetrics(symbol="BTC", regulatory_status=RegulatoryStatus.CLEAR, rwa_tvl_usd=1.5e9, rwa_growth_30d_pct=8, recent_product_launches=3, ecosystem_score=95, macro_liquidity_score=70, network_upgrade_score=75, staking_etf_available=True, net_capital_flow_30d=15, cycle_phase=NetworkPhase.BULL_RUN, active_addresses_30d_pct=5, real_usage_score=90, circulating_supply=19.7e6, total_supply=19.7e6, max_supply=21e6, annual_inflation_pct=0.8, unlock_30d_pct=0, unlock_90d_pct=0, team_investor_pct=0, top10_holder_pct=5, annual_fees_usd=1.2e9, annual_revenue_usd=8e8, annual_burn_usd=0, staking_yield_pct=0, daily_volume_usd=2.5e10, price=65000, mcap_usd=1.28e12, fdv_usd=1.365e12, price_ath=73750, price_200d_avg=55000, active_addresses=900000),
    "ETH": TokenMetrics(symbol="ETH", regulatory_status=RegulatoryStatus.COMPLIANT, rwa_tvl_usd=8e9, rwa_growth_30d_pct=12, recent_product_launches=4, ecosystem_score=98, macro_liquidity_score=68, network_upgrade_score=90, staking_etf_available=True, net_capital_flow_30d=10, cycle_phase=NetworkPhase.UPGRADE_CATALYST, active_addresses_30d_pct=4, real_usage_score=95, circulating_supply=120e6, total_supply=120e6, max_supply=0, annual_inflation_pct=0.5, unlock_30d_pct=0, unlock_90d_pct=0, team_investor_pct=0, top10_holder_pct=8, annual_fees_usd=2.5e9, annual_revenue_usd=1.8e9, annual_burn_usd=5e8, staking_yield_pct=3.5, daily_volume_usd=1.5e10, price=3500, mcap_usd=4.2e11, fdv_usd=4.2e11, price_ath=4878, price_200d_avg=2800, active_addresses=500000),
    "SOL": TokenMetrics(symbol="SOL", regulatory_status=RegulatoryStatus.PENDING, rwa_tvl_usd=5e8, rwa_growth_30d_pct=20, recent_product_launches=5, ecosystem_score=88, macro_liquidity_score=65, network_upgrade_score=80, staking_etf_available=True, net_capital_flow_30d=20, cycle_phase=NetworkPhase.UPGRADE_CATALYST, active_addresses_30d_pct=10, real_usage_score=85, circulating_supply=440e6, total_supply=580e6, max_supply=0, annual_inflation_pct=5, unlock_30d_pct=2, unlock_90d_pct=5, team_investor_pct=20, top10_holder_pct=25, annual_fees_usd=1.5e8, annual_revenue_usd=1e8, annual_burn_usd=3e7, staking_yield_pct=6.5, daily_volume_usd=3e9, price=150, mcap_usd=6.6e10, fdv_usd=8.7e10, price_ath=260, price_200d_avg=120, active_addresses=1200000),
    "ONDO": TokenMetrics(symbol="ONDO", regulatory_status=RegulatoryStatus.COMPLIANT, rwa_tvl_usd=8e8, rwa_growth_30d_pct=35, recent_product_launches=3, ecosystem_score=82, macro_liquidity_score=70, network_upgrade_score=65, staking_etf_available=False, net_capital_flow_30d=25, cycle_phase=NetworkPhase.BULL_RUN, active_addresses_30d_pct=15, real_usage_score=75, circulating_supply=1.4e9, total_supply=1e10, max_supply=1e10, annual_inflation_pct=15, unlock_30d_pct=5, unlock_90d_pct=12, team_investor_pct=35, top10_holder_pct=45, annual_fees_usd=2e7, annual_revenue_usd=1.5e7, annual_burn_usd=0, staking_yield_pct=0, daily_volume_usd=2e8, price=0.85, mcap_usd=1.19e9, fdv_usd=8.5e9, price_ath=1.5, price_200d_avg=0.7, active_addresses=50000),
    "MATIC": TokenMetrics(symbol="MATIC", regulatory_status=RegulatoryStatus.COMPLIANT, rwa_tvl_usd=2e8, rwa_growth_30d_pct=15, recent_product_launches=2, ecosystem_score=80, macro_liquidity_score=60, network_upgrade_score=85, staking_etf_available=False, net_capital_flow_30d=5, cycle_phase=NetworkPhase.ACCUMULATION, active_addresses_30d_pct=3, real_usage_score=78, circulating_supply=9.3e9, total_supply=1e10, max_supply=1e10, annual_inflation_pct=3, unlock_30d_pct=1, unlock_90d_pct=3, team_investor_pct=15, top10_holder_pct=20, annual_fees_usd=5e7, annual_revenue_usd=3.5e7, annual_burn_usd=1e7, staking_yield_pct=5, daily_volume_usd=4e8, price=0.7, mcap_usd=6.51e9, fdv_usd=7e9, price_ath=2.92, price_200d_avg=0.65, active_addresses=300000),
    "LINK": TokenMetrics(symbol="LINK", regulatory_status=RegulatoryStatus.COMPLIANT, rwa_tvl_usd=1.5e8, rwa_growth_30d_pct=25, recent_product_launches=3, ecosystem_score=85, macro_liquidity_score=62, network_upgrade_score=70, staking_etf_available=False, net_capital_flow_30d=12, cycle_phase=NetworkPhase.UPGRADE_CATALYST, active_addresses_30d_pct=8, real_usage_score=80, circulating_supply=587e6, total_supply=1e9, max_supply=1e9, annual_inflation_pct=4, unlock_30d_pct=1.5, unlock_90d_pct=4, team_investor_pct=25, top10_holder_pct=30, annual_fees_usd=8e7, annual_revenue_usd=6e7, annual_burn_usd=5e6, staking_yield_pct=4.5, daily_volume_usd=5e8, price=14.5, mcap_usd=8.5e9, fdv_usd=1.45e10, price_ath=52.7, price_200d_avg=12, active_addresses=200000),
    "AAVE": TokenMetrics(symbol="AAVE", regulatory_status=RegulatoryStatus.COMPLIANT, rwa_tvl_usd=1.2e10, rwa_growth_30d_pct=18, recent_product_launches=2, ecosystem_score=82, macro_liquidity_score=64, network_upgrade_score=75, staking_etf_available=False, net_capital_flow_30d=8, cycle_phase=NetworkPhase.ACCUMULATION, active_addresses_30d_pct=6, real_usage_score=85, circulating_supply=14.8e6, total_supply=16e6, max_supply=16e6, annual_inflation_pct=2, unlock_30d_pct=0.5, unlock_90d_pct=1.5, team_investor_pct=20, top10_holder_pct=25, annual_fees_usd=1.2e8, annual_revenue_usd=9e7, annual_burn_usd=2e7, staking_yield_pct=6, daily_volume_usd=3e8, price=150, mcap_usd=2.22e9, fdv_usd=2.4e9, price_ath=666, price_200d_avg=130, active_addresses=50000),
    "UNI": TokenMetrics(symbol="UNI", regulatory_status=RegulatoryStatus.COMPLIANT, rwa_tvl_usd=5e9, rwa_growth_30d_pct=10, recent_product_launches=2, ecosystem_score=78, macro_liquidity_score=60, network_upgrade_score=70, staking_etf_available=False, net_capital_flow_30d=3, cycle_phase=NetworkPhase.ACCUMULATION, active_addresses_30d_pct=4, real_usage_score=75, circulating_supply=600e6, total_supply=1e9, max_supply=1e9, annual_inflation_pct=2.5, unlock_30d_pct=1, unlock_90d_pct=3, team_investor_pct=30, top10_holder_pct=35, annual_fees_usd=4e8, annual_revenue_usd=3e8, annual_burn_usd=0, staking_yield_pct=3, daily_volume_usd=2e8, price=7.5, mcap_usd=4.5e9, fdv_usd=7.5e9, price_ath=44.92, price_200d_avg=6.5, active_addresses=150000),
}


def _calc_adx(high, low, close, period=14):
    plus_dm = np.diff(high)
    minus_dm = np.diff(low) * -1
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    tr1 = high[1:] - low[1:]
    tr2 = np.abs(high[1:] - close[:-1])
    tr3 = np.abs(low[1:] - close[:-1])
    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    atr = pd.Series(tr).ewm(alpha=1/period, min_periods=period).mean().values
    plus_di = 100 * pd.Series(plus_dm).ewm(alpha=1/period, min_periods=period).mean().values / (atr + 1e-10)
    minus_di = 100 * pd.Series(minus_dm).ewm(alpha=1/period, min_periods=period).mean().values / (atr + 1e-10)
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
    adx = pd.Series(dx).ewm(alpha=1/period, min_periods=period).mean().values
    return adx, plus_di, minus_di


def gen_ohlcv(m: TokenMetrics, n: int, seed: int) -> pd.DataFrame:
    np.random.seed(seed)
    vol = 0.02 * (0.8 if m.real_usage_score > 80 else 1.5)
    drift = m.rwa_growth_30d_pct / 100 / 30
    phi = 0.35
    noise = np.random.normal(0, vol, n)
    rets = np.zeros(n)
    rets[0] = np.random.normal(drift, vol)
    for t in range(1, n):
        rets[t] = phi * rets[t-1] + noise[t]
        rets[t] += drift
    price = m.price * np.exp(np.cumsum(rets))
    dates = pd.date_range(end=pd.Timestamp.now(), periods=n, freq='1h')
    o = price * (1 + np.random.uniform(-0.003, 0.003, n))
    h = price * (1 + np.random.uniform(0.005, 0.015, n))
    l = price * (1 - np.random.uniform(0.005, 0.015, n))
    c = price
    base_vol = m.daily_volume_usd * 0.03 if m.daily_volume_usd > 0 else 5e7
    trend = np.where(rets > 0, 1.3, 0.7)
    vol_mult = np.random.uniform(0.8, 1.5, n)
    volume = base_vol * trend * vol_mult
    return pd.DataFrame({'open': o, 'high': h, 'low': l, 'close': c, 'volume': volume}, index=dates)


def run_one(m: TokenMetrics, seed: int, periods: int = 500) -> Optional[Dict]:
    enh = compute_enhanced_token_score(m)
    timing = estimate_timing_quality(m)
    if enh['total'] < 55 or timing < 0.35:
        return None
    df = gen_ohlcv(m, periods, seed)
    eng = SmartEntryEngine(min_rr=2.0)
    trades = []
    i = 50
    while i < len(df) - 50:
        if i < 51:
            i += 1
            continue
        c = df['close'].values[:i+1]
        h = df['high'].values[:i+1]
        l = df['low'].values[:i+1]
        v = df['volume'].values[:i+1]
        e20 = pd.Series(c).ewm(span=20).mean()
        e50 = pd.Series(c).ewm(span=50).mean()
        if e20.iloc[-2] <= e50.iloc[-2] and e20.iloc[-1] > e50.iloc[-1]:
            side = "BUY"
        elif e20.iloc[-2] >= e50.iloc[-2] and e20.iloc[-1] < e50.iloc[-1]:
            side = "SELL"
        else:
            i += 1
            continue
        if i < 50:
            i += 1
            continue
        adx_vals, plus_di, minus_di = _calc_adx(h, l, c)
        adx = adx_vals[-1] if len(adx_vals) > 0 else 0
        if adx <= 20:
            i += 1
            continue
        if side == "BUY" and c[-1] <= e50.iloc[-1]:
            i += 1
            continue
        if side == "SELL" and c[-1] >= e50.iloc[-1]:
            i += 1
            continue
        vol_avg = pd.Series(v).rolling(20).mean().iloc[-1]
        if v[-1] <= vol_avg:
            i += 1
            continue
        entry = float(c[-1])
        atr = float(pd.Series(c).diff().abs().rolling(14).mean().iloc[-1])
        atr = max(atr, entry * 0.002)
        regime = "STRONG_TREND" if m.cycle_phase in (NetworkPhase.BULL_RUN, NetworkPhase.UPGRADE_CATALYST) else "RANGING"
        plan = eng.build_plan(side, entry, atr, regime)
        future = df.iloc[i+1:min(i+1+250, len(df))]
        if len(future) < 10:
            break
        res = eng.simulate(plan, future)
        trades.append({'pnl': res.pnl_pct, 'won': res.won})
        i += 15
    if not trades:
        return None
    pnls = [t['pnl'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    tw = len(trades)
    ww = len(wins)
    wr = ww/tw*100 if tw > 0 else 0
    tp = sum(pnls)
    aw = np.mean(wins) if wins else 0
    al = np.mean(losses) if losses else 0
    pf = sum(wins)/abs(sum(losses)) if losses and sum(losses) != 0 else (10 if wins else 0)
    exp = (wr/100*aw) + ((1-wr/100)*al)
    eq = [100]
    for p in pnls:
        eq.append(eq[-1]*(1+p/100))
    peak = eq[0]
    mdd = 0
    for e in eq:
        if e > peak: peak = e
        dd = (peak-e)/peak*100
        if dd > mdd: mdd = dd
    rets = np.diff(eq)/eq[:-1] if len(eq) > 1 else [0]
    sharpe = float(np.mean(rets)/np.std(rets)*np.sqrt(252)) if np.std(rets) > 0 else 0
    neg = rets[rets<0]
    sortino = float(np.mean(rets)/np.std(neg)*np.sqrt(252)) if len(neg) > 0 and np.std(neg) > 0 else 0
    calmar = float(tp/mdd) if mdd > 0 else 0
    return {'symbol': m.symbol, 'seed': seed, 'enhanced_score': enh['total'], 'base_score': enh['base_score'], 'dilution': enh['dilution_score'], 'capture': enh['capture_score'], 'valuation': enh['valuation_grade'], 'upside': enh['upside_potential_pct'], 'rr': enh['risk_reward_ratio'], 'timing': timing, 'trades': tw, 'wins': ww, 'losses': tw-ww, 'win_rate': round(wr,1), 'pnl': round(tp,2), 'pf': round(pf,2), 'exp': round(exp,3), 'mdd': round(mdd,1), 'sharpe': round(sharpe,2), 'sortino': round(sortino,2), 'calmar': round(calmar,2), 'aw': round(aw,2), 'al': round(al,2)}


def run_heavy(seeds: List[int], periods: int = 500) -> Dict:
    results = []
    for sym, m in TOKENS.items():
        for s in seeds:
            r = run_one(m, s, periods)
            if r:
                results.append(r)
    if not results:
        return {'error': 'No results'}
    all_p = [t['pnl'] for r in results for t in [{'pnl': r['pnl']}]]
    total_t = sum(r['trades'] for r in results)
    total_w = sum(r['wins'] for r in results)
    wr = total_w/total_t*100 if total_t > 0 else 0
    tp = sum(r['pnl'] for r in results)
    pf_vals = [r['pf'] for r in results]
    avg_pf = np.mean(pf_vals) if pf_vals else 0
    sharpe_vals = [r['sharpe'] for r in results]
    avg_sharpe = np.mean(sharpe_vals) if sharpe_vals else 0
    mdd_vals = [r['mdd'] for r in results]
    max_mdd = max(mdd_vals) if mdd_vals else 0
    exp_vals = [r['exp'] for r in results]
    avg_exp = np.mean(exp_vals) if exp_vals else 0
    tok_summ = {}
    for sym in TOKENS:
        tr = [r for r in results if r['symbol'] == sym]
        if not tr:
            continue
        tt = sum(r['trades'] for r in tr)
        tw = sum(r['wins'] for r in tr)
        tok_summ[sym] = {'runs': len(tr), 'trades': tt, 'wr': round(tw/tt*100,1) if tt > 0 else 0, 'pnl': round(sum(r['pnl'] for r in tr),1), 'pf': round(np.mean([r['pf'] for r in tr]),2), 'sharpe': round(np.mean([r['sharpe'] for r in tr]),2), 'score': round(np.mean([r['enhanced_score'] for r in tr]),1), 'pass': (tw/tt*100 >= 50 and np.mean([r['pf'] for r in tr]) >= 1.5) if tt > 0 else False}
    seed_summ = {}
    for s in seeds:
        sr = [r for r in results if r['seed'] == s]
        if not sr:
            continue
        tt = sum(r['trades'] for r in sr)
        tw = sum(r['wins'] for r in sr)
        seed_summ[s] = {'runs': len(sr), 'trades': tt, 'wr': round(tw/tt*100,1) if tt > 0 else 0, 'pnl': round(sum(r['pnl'] for r in sr),1), 'pf': round(np.mean([r['pf'] for r in sr]),2), 'pass': (tw/tt*100 >= 50 and np.mean([r['pf'] for r in sr]) >= 1.5) if tt > 0 else False}
    tpr = sum(1 for t in tok_summ.values() if t['pass'])/len(tok_summ)*100 if tok_summ else 0
    spr = sum(1 for s in seed_summ.values() if s['pass'])/len(seed_summ)*100 if seed_summ else 0
    if wr >= 60 and avg_pf >= 2.0 and avg_sharpe >= 1.5: grade = "A+ (EXCELLENT)"
    elif wr >= 55 and avg_pf >= 1.8 and avg_sharpe >= 1.0: grade = "A (STRONG)"
    elif wr >= 50 and avg_pf >= 1.5: grade = "B (GOOD)"
    elif wr >= 45 and avg_pf >= 1.2: grade = "C (FAIR)"
    elif wr >= 40: grade = "D (WEAK)"
    else: grade = "F (POOR)"
    return {'results': results, 'overview': {'total_runs': len(TOKENS)*len(seeds), 'valid': len(results), 'trades': total_t, 'tokens': len(TOKENS), 'seeds': len(seeds)}, 'perf': {'wr': round(wr,1), 'pnl': round(tp,1), 'pf': round(avg_pf,2), 'exp': round(avg_exp,3), 'mdd': round(max_mdd,1), 'sharpe': round(avg_sharpe,2), 'sortino': round(np.mean([r['sortino'] for r in results]),2), 'calmar': round(np.mean([r['calmar'] for r in results]),2)}, 'pass_rates': {'token': round(tpr,1), 'seed': round(spr,1), 'tok_pass': sum(1 for t in tok_summ.values() if t['pass']), 'seed_pass': sum(1 for s in seed_summ.values() if s['pass'])}, 'grade': grade, 'tokens': tok_summ, 'seeds': seed_summ}


def main():
    print("="*80)
    print("  HEAVY FUNDAMENTAL BACKTEST — ESMH.TRADE")
    print("="*80)
    econ = compute_economic_quality(MacroData(global_m2_yoy_pct=3.5, fed_policy_rate=4.5, vix=18, credit_spread_bps=180, dxy_yoy_pct=-2, correlation_risk=0.45, inflation_yoy_pct=2.8, unemployment_rate=3.9))
    print(f"\n[ECONOMIC QUALITY] Score: {econ['score']}/100 | Regime: {econ['regime']} | Liquidity: {econ['liquidity_condition']}")
    seeds = [7,13,21,42,99,123,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500]
    print(f"\n[RUNNING] {len(TOKENS)} tokens x {len(seeds)} seeds = {len(TOKENS)*len(seeds)} combinations...")
    res = run_heavy(seeds, 500)
    if 'error' in res:
        print(f"ERROR: {res['error']}")
        return
    ov = res['overview']
    pf = res['perf']
    pr = res['pass_rates']
    print(f"\n[RESULTS] Valid: {ov['valid']}/{ov['total_runs']} | Trades: {ov['trades']}")
    print(f"\n  Win Rate:      {pf['wr']}%")
    print(f"  Profit Factor: {pf['pf']}")
    print(f"  Total PnL:     {pf['pnl']}%")
    print(f"  Expectancy:    {pf['exp']}%")
    print(f"  Max Drawdown:  {pf['mdd']}%")
    print(f"  Sharpe:        {pf['sharpe']}")
    print(f"  Sortino:       {pf['sortino']}")
    print(f"  Calmar:        {pf['calmar']}")
    print(f"\n  Token Pass: {pr['token']}% ({pr['tok_pass']}/{len(res['tokens'])})")
    print(f"  Seed Pass:  {pr['seed']}% ({pr['seed_pass']}/{len(res['seeds'])})")
    print(f"\n  GRADE: {res['grade']}")
    print(f"\n[PER-TOKEN] {'Sym':<6}{'Runs':>5}{'Trades':>7}{'WR%':>6}{'PF':>6}{'PnL%':>7}{'Score':>6}{'Pass':>5}")
    for sym, t in sorted(res['tokens'].items(), key=lambda x: x[1]['wr'], reverse=True):
        print(f"          {sym:<6}{t['runs']:>5}{t['trades']:>7}{t['wr']:>6.1f}{t['pf']:>6.2f}{t['pnl']:>7.1f}{t['score']:>6.1f}{'PASS' if t['pass'] else 'FAIL':>5}")
    print(f"\n[PER-SEED] {'Seed':>5}{'Runs':>5}{'Trades':>7}{'WR%':>6}{'PF':>6}{'PnL%':>7}{'Pass':>5}")
    for s, t in sorted(res['seeds'].items()):
        print(f"          {s:>5}{t['runs']:>5}{t['trades']:>7}{t['wr']:>6.1f}{t['pf']:>6.2f}{t['pnl']:>7.1f}{'PASS' if t['pass'] else 'FAIL':>5}")
    print("\n"+"="*80)
    if res['grade'].startswith('A'):
        print("  SYSTEM IS POWERFUL - Ready for deployment")
    elif res['grade'].startswith('B'):
        print("  SYSTEM IS STRONG - Minor optimizations recommended")
    else:
        print("  SYSTEM NEEDS IMPROVEMENT")
    print("="*80)
    return res

if __name__ == "__main__":
    main()
