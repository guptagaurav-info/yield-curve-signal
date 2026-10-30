"""Run the study end to end: data -> episodes -> probit -> de-risking rules -> metrics.json + figures."""
import json
from pathlib import Path

import scipy.stats as st
import yaml

from . import analysis as A
from . import data, figures as F


def main(cfg_path="configs/default.yaml"):
    cfg = yaml.safe_load(open(cfg_path)); out = Path("reports"); (out / "figures").mkdir(parents=True, exist_ok=True)
    m = data.monthly(cfg)
    eps = A.episodes(m["spread"], cfg["min_inverted_months"], cfg["merge_gap_months"])
    tab = A.episode_table(m, eps)
    eps2 = A.episodes(m["spread_2y"], cfg["min_inverted_months"], cfg["merge_gap_months"])
    tab2 = A.episode_table(m.assign(spread=m["spread_2y"]), eps2)
    pr, d = A.probit(m, cfg["horizon_months"])
    p_now = float(st.norm.cdf(pr.params["const"] + pr.params["x"] * m["spread"].iloc[-1] / 100))
    p_at = {f"{s:+.1f} pp": float(st.norm.cdf(pr.params["const"] + pr.params["x"] * s / 100)) for s in [-1.5, -0.5, 0, 0.5, 1, 2]}
    R, cash, tc = A.rules(m)
    rules = {c: {"ann_return": A.ann(R[c]), "vol": A.vol(R[c]), "max_dd": A.mdd(R[c]), "sharpe": (A.ann(R[c]) - A.ann(cash)) / A.vol(R[c]), "time_in_cash": tc[c]} for c in R}
    res = {"sample": {"curve_start": str(m.index[0].date()), "end": str(m.index[-1].date()), "equity_start": str(R.index[0].date()), "months": len(m)},
           "now": {"spread_10y3m_pp": float(m["spread"].iloc[-1]), "spread_10y2y_pp": float(m["spread_2y"].iloc[-1]), "bill": float(m["bill"].iloc[-1]), "probit_p12": p_now},
           "episodes_10y3m": tab.to_dict("records"), "episodes_10y2y": tab2.to_dict("records"),
           "probit": {"const": float(pr.params["const"]), "slope_per_pp": float(pr.params["x"] / 100), "pseudo_r2": float(pr.prsquared), "n": int(pr.nobs),
                      "fit_end": str(d.index[-1].date()), "p_at_spread": p_at, "note": "in-sample; four recessions; descriptive only"},
           "rules": rules}
    json.dump(res, open(out / "metrics.json", "w"), indent=2, default=lambda x: None if x != x else float(x))
    tab.to_csv(out / "episodes.csv", index=False); m.to_csv(out / "monthly.csv")
    F.spread_chart(m, eps, out / "figures/spread.png"); F.episodes_chart(tab, out / "figures/episodes.png")
    F.spy_path(m, eps, out / "figures/spy_after.png"); F.rules_chart(R, out / "figures/rules.png")
    print(tab.to_string()); print(tab2.to_string()); print(json.dumps(res["now"])); print(json.dumps(rules, indent=0, default=float)); print(res["probit"])
    return res


if __name__ == "__main__":
    main()
