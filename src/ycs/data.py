"""Monthly yield-curve spreads, SPY total returns, T-bill cash and an NBER recession flag."""
import pandas as pd
import pyarrow.parquet as pq

RAW = "data/raw/"


def curve():
    y = pq.read_table(RAW + "daily_treasury_yield.parquet").to_pandas()
    y.index = pd.to_datetime(y.pop("report_date"))
    return y.astype(float).sort_index()


def spy_total_return(sym="SPY"):
    px = pq.read_table(RAW + "stock_prices.parquet", columns=["symbol", "report_date", "close"], filters=[("symbol", "=", sym)]).to_pandas()
    px.index = pd.to_datetime(px.pop("report_date")); px = px["close"].astype(float).sort_index()
    dv = pq.read_table(RAW + "stock_dividend_events.parquet", filters=[("symbol", "=", sym)]).to_pandas()
    dv.index = pd.to_datetime(dv.pop("report_date")); dv = dv["amount"].astype(float).groupby(level=0).sum().reindex(px.index).fillna(0.0)
    return ((px + dv) / px.shift(1) - 1).iloc[1:]


def recession_flag(index, periods):
    f = pd.Series(0, index=index)
    for a, b in periods:
        f[(index >= pd.Period(a, "M").to_timestamp()) & (index <= pd.Period(b, "M").to_timestamp("M"))] = 1
    return f


def monthly(cfg):
    y = curve()
    m = pd.DataFrame({"spread": (y[cfg["spread"][0]] - y[cfg["spread"][1]]) * 100,
                      "spread_2y": (y[cfg["alt_spread"][0]] - y[cfg["alt_spread"][1]]) * 100,
                      "bill": y["bc_3month"]}).resample("ME").mean()
    r = spy_total_return(cfg["equity"])
    m["spy"] = (1 + r).resample("ME").prod() - 1
    m.loc[m.index < pd.Timestamp(cfg["start_equity"]), "spy"] = float("nan")
    m["cash"] = m["bill"].shift(1) / 12                     # bill yield known at the start of the month
    m["recession"] = recession_flag(m.index, cfg["recessions"])
    last_full = r.index[-1].to_period("M").to_timestamp("M")
    if r.index[-1] < last_full - pd.Timedelta(days=3): m = m.iloc[:-1]   # drop a partial final month
    return m
