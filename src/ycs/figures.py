import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

NAVY, GOLD, GREY, RED, TEAL = "#1f3a5f", "#c9a227", "#8a8f98", "#b23a3a", "#2a7f7f"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold",
                     "axes.titlesize": 12.5, "figure.dpi": 150, "savefig.bbox": "tight"})


def shade(ax, m):
    r = m["recession"]; on = None
    for d, v in r.items():
        if v and on is None: on = d
        if not v and on is not None: ax.axvspan(on, d, color=GREY, alpha=0.25, lw=0); on = None


def spread_chart(m, eps, path):
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    shade(ax, m)
    ax.plot(m.index, m["spread"], color=NAVY, lw=1.6, label="10-year minus 3-month Treasury (monthly average)")
    ax.fill_between(m.index, m["spread"], 0, where=m["spread"] < 0, color=RED, alpha=0.35, lw=0, label="Inverted")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("Percentage points"); ax.xaxis.set_major_locator(mdates.YearLocator(4)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_title("The yield curve and US recessions (grey), 1990–2026")
    ax.legend(frameon=False, loc="lower left", fontsize=9); fig.savefig(path); plt.close(fig)


def episodes_chart(tab, path):
    fig, ax = plt.subplots(figsize=(10.5, 4.4))
    x = np.arange(len(tab)); labels = [f"{r.start} → {r.end}\n({r.months} months)" for r in tab.itertuples()]
    v = [0 if r.lead_months != r.lead_months or r.lead_months is None else r.lead_months for r in tab.itertuples()]
    cols = [TEAL if (r.recession_start is not None and r.recession_start == r.recession_start) else RED for r in tab.itertuples()]
    b = ax.bar(x, v, color=cols)
    for xi, r, vv in zip(x, tab.itertuples(), v):
        t = f"Recession {r.recession_start}\nafter {int(vv)} months" if vv else "No recession\n(through Oct 2026)"
        ax.text(xi, vv + 0.4, t, ha="center", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.5); ax.set_ylim(0, 22)
    ax.set_ylabel("Months from first inversion to recession"); ax.set_title("Five inversions since 2000: three recessions, two misses")
    fig.savefig(path); plt.close(fig)


def spy_path(m, eps, path):
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    for (a, b, n), c in zip(eps, [NAVY, GOLD, TEAL, RED, GREY]):
        s = m["spy"].loc[a:].dropna().iloc[:37]
        ax.plot(range(len(s) + 1), np.r_[1, (1 + s).cumprod()] * 100, color=c, lw=2, label=f"From {a:%b %Y}")
    ax.axhline(100, color="black", lw=0.6); ax.set_xlabel("Months after the curve first inverted"); ax.set_ylabel("S&P 500 total return (start = 100)")
    ax.set_title("What stocks did after the curve inverted"); ax.legend(frameon=False, fontsize=9); fig.savefig(path); plt.close(fig)


def rules_chart(R, path):
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    for c, col in zip(R.columns, [NAVY, RED, TEAL, GOLD]):
        ax.plot(R.index, (1 + R[c]).cumprod(), color=col, lw=2 if c.startswith("Buy") else 1.5, label=c)
    ax.set_yscale("log"); ax.set_ylabel("Growth of $1 (log scale)"); ax.xaxis.set_major_locator(mdates.YearLocator(4)); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_title("Selling stocks on an inverted curve, 1996–2026"); ax.legend(frameon=False, fontsize=9); fig.savefig(path); plt.close(fig)
