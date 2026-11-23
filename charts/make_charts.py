"""README charts from the gold marts. Usage: python charts/make_charts.py [--db warehouse/claims.duckdb] [--out docs/charts]"""
import argparse
from pathlib import Path

import duckdb
import matplotlib.dates as mdates

import style as st

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("--db", default=str(ROOT / "warehouse" / "claims.duckdb"))
ap.add_argument("--out", default=str(ROOT / "docs" / "charts"))
a = ap.parse_args()
OUT = Path(a.out)
con = duckdb.connect(a.db, read_only=True)

# 1. Paid per member per month by chronic-condition burden
p = con.execute("""select year, chronic_band, inpatient_pmpm_usd::double, outpatient_pmpm_usd::double
                   from gold.rpt_cost_pmpm order by year, chronic_band""").fetchall()
years = sorted({r[0] for r in p})
bands = sorted({r[1] for r in p}, key=lambda b: int(b.rstrip("+").split("-")[0]))
f, ax = st.fig(8, 3.5)
w = 0.8 / len(years)
for j, yr in enumerate(years):
    vals = [next((r[2] + r[3] for r in p if r[0] == yr and r[1] == b), 0) for b in bands]
    bars = ax.bar([i - 0.4 + w * (j + 0.5) for i in range(len(bands))], vals, w * 0.92, color=st.S[j], label=str(yr))
    st.vbar_labels(ax, bars, lambda v: f"${v:,.0f}")
ax.set_xticks(range(len(bands)), [f"{b} chronic conditions" for b in bands])
ax.yaxis.set_major_formatter(st.FuncFormatter(lambda v, _: f"${v:,.0f}"))
first = [r for r in p if r[0] == years[0]]
lo, hi = first[0][2] + first[0][3], first[-1][2] + first[-1][3]
st.head(ax, f"Members with 5+ chronic conditions cost {hi / lo:,.0f}x those with none ({years[0]})",
        "Paid per member per month, inpatient + outpatient, CMS synthetic Medicare claims", legend=True)
st.save(f, OUT / "pmpm_by_burden.png")

# 2. Pre-authorisation turnaround by month and priority
m = con.execute("""select submitted_month, priority, median_turnaround_hours, p90_turnaround_hours, requests
                   from gold.rpt_preauth_monthly where requests >= 50 order by 1, 2""").fetchall()
f, ax = st.fig(8, 3.4)
for i, (pr, dl) in enumerate([("urgent", 72), ("standard", 168)]):
    rows = [r for r in m if r[1] == pr]
    x = [r[0] for r in rows]
    ax.fill_between(x, [r[2] for r in rows], [r[3] for r in rows], color=st.S[i], alpha=0.15, lw=0)
    ax.plot(x, [r[2] for r in rows], color=st.S[i], lw=2, label=f"{pr.title()}: median, band to p90 (deadline {dl} h)")
ax.axhline(72, color=st.MUTED, lw=1, ls="--", label="72-hour urgent deadline")
ax.set_ylim(0, 100)
ax.set_ylabel("Hours to decision")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
st.head(ax, "Pre-authorisations are decided well inside CMS deadlines",
        "Hours from submission to decision, excluding time pended for information (synthetic events)", legend=True, ncol=2)
st.save(f, OUT / "preauth_turnaround.png")
print(f"wrote charts to {OUT}")
