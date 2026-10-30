"""Inversion episodes, a recession probit, and simple de-risking rules tested month by month."""
import numpy as np
import pandas as pd
import statsmodels.api as sm

ann = lambda r: (1 + r).prod() ** (12 / len(r)) - 1
vol = lambda r: r.std() * np.sqrt(12)
mdd = lambda r: ((1 + r).cumprod() / (1 + r).cumprod().cummax() - 1).min()


def episodes(spread, min_months, gap):
    inv = spread[spread < 0].index
    eps, cur = [], []
    for d in inv:
        if cur and (d.to_period("M") - cur[-1].to_period("M")).n > gap: eps.append(cur); cur = []
        cur.append(d)
    if cur: eps.append(cur)
    return [(e[0], e[-1], len(e)) for e in eps if len(e) >= min_months]


def next_recession_start(m, after):
    r = m["recession"]; starts = r.index[(r == 1) & (r.shift(1, fill_value=0) == 0)]
    s = starts[starts >= after]
    return s[0] if len(s) else None


def episode_table(m, eps, horizon=24):
    rows = []
    for a, b, n in eps:
        rs = next_recession_start(m, a)
        lead = (rs.to_period("M") - a.to_period("M")).n if rs is not None else None
        hit = lead is not None and lead <= horizon
        s = m["spy"].loc[a:].dropna()
        w = s.iloc[:24]
        row = {"start": a.strftime("%Y-%m"), "end": b.strftime("%Y-%m"), "months": n, "min_spread_pp": float(m["spread"].loc[a:b].min()),
               "recession_start": rs.strftime("%Y-%m") if rs is not None and hit else None, "lead_months": lead if hit else None,
               "spy_to_recession": float((1 + m["spy"].loc[a:rs].iloc[:-1]).prod() - 1) if hit and len(m["spy"].loc[a:rs].dropna()) else None,
               "spy_next12": float((1 + s.iloc[:12]).prod() - 1) if len(s) >= 12 else None,
               "spy_maxdd_24m": float(mdd(w)) if len(w) else None}
        rows.append(row)
    return pd.DataFrame(rows)


def probit(m, horizon):
    target = m["recession"][::-1].rolling(horizon, min_periods=1).max()[::-1].shift(-1)   # any recession month in t+1..t+h
    d = pd.DataFrame({"y": target, "x": m["spread"] / 100}).dropna()
    d = d[d.index <= m.index[-1] - pd.DateOffset(months=horizon)]                        # only months whose outcome is known
    r = sm.Probit(d["y"], sm.add_constant(d["x"])).fit(disp=0)
    return r, d


def rules(m):
    """Signals at month-end t are applied to month t+1. Cash = 3-month bill."""
    sig_inv = (m["spread"] < 0).astype(float).shift(1).fillna(0)
    # 'after un-inversion': for 12 months after the curve turns positive following >= 3 inverted months
    inv = (m["spread"] < 0).astype(int); run = inv.groupby((inv != inv.shift()).cumsum()).cumsum()
    turned = (inv == 0) & (inv.shift(1) == 1) & (run.shift(1) >= 3)
    after = pd.Series(0.0, index=m.index)
    for d in m.index[turned]: after.loc[d:d + pd.DateOffset(months=11)] = 1.0
    after = after.shift(1).fillna(0)
    d = m.dropna(subset=["spy", "cash"])
    out = {"Buy and hold SPY": d["spy"],
           "Cash while the curve is inverted": d["spy"] * (1 - sig_inv.loc[d.index]) + d["cash"] * sig_inv.loc[d.index],
           "Cash for 12 months after it un-inverts": d["spy"] * (1 - after.loc[d.index]) + d["cash"] * after.loc[d.index],
           "Half cash while inverted": d["spy"] * (1 - 0.5 * sig_inv.loc[d.index]) + d["cash"] * 0.5 * sig_inv.loc[d.index]}
    time_cash = {"Cash while the curve is inverted": float(sig_inv.loc[d.index].mean()), "Cash for 12 months after it un-inverts": float(after.loc[d.index].mean()),
                 "Half cash while inverted": float(0.5 * sig_inv.loc[d.index].mean()), "Buy and hold SPY": 0.0}
    return pd.DataFrame(out), d["cash"], time_cash
