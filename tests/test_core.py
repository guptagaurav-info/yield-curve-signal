import numpy as np
import pandas as pd

from ycs import analysis as A, data


def _m(n=60):
    idx = pd.date_range("2000-01-31", periods=n, freq="ME")
    s = pd.Series(1.0, index=idx); s.iloc[10:16] = -0.5; s.iloc[30:31] = -0.2
    return pd.DataFrame({"spread": s, "spy": 0.01, "cash": 0.002, "recession": 0}, index=idx)


def test_episodes_need_three_months():
    eps = A.episodes(_m()["spread"], 3, 3)
    assert len(eps) == 1 and eps[0][2] == 6            # the 1-month dip is not an episode


def test_signal_applies_next_month_only():
    m = _m(); R, cash, tc = A.rules(m)
    r = R["Cash while the curve is inverted"]
    assert r.iloc[10] == 0.01 and r.iloc[11] == 0.002   # inverted at end of month 10 -> cash in month 11, not 10


def test_recession_flag():
    idx = pd.date_range("2007-10-31", periods=6, freq="ME")
    f = data.recession_flag(idx, [["2007-12", "2008-02"]])
    assert list(f) == [0, 0, 1, 1, 1, 0]


def test_after_uninversion_window_is_12_months():
    m = _m(); R, cash, tc = A.rules(m)
    r = R["Cash for 12 months after it un-inverts"]
    assert (r.iloc[17:29] == 0.002).all() and r.iloc[29] == 0.01
