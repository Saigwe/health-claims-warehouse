"""Write the day's operational KPIs (the last DAG task): requests submitted and decided that day, approvals,
SLA misses, requests still open, and the running control-exception total. One JSON file per logical date.

Usage: python analysis/daily_kpis.py --db warehouse/claims.duckdb --ds 2009-03-02 --out results/daily
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="warehouse/claims.duckdb")
    ap.add_argument("--ds", required=True)
    ap.add_argument("--out", type=Path, default=Path("results/daily"))
    args = ap.parse_args()
    con = duckdb.connect(args.db, read_only=True)
    row = con.execute("""
        select
            count(*) filter (where cast(submitted_at as date) = ?)                        as submitted,
            count(*) filter (where cast(decided_at as date) = ?)                          as decided,
            count(*) filter (where cast(decided_at as date) = ? and status = 'approved')  as approved,
            count(*) filter (where cast(decided_at as date) = ? and not met_sla)          as sla_missed,
            count(*) filter (where cast(submitted_at as date) <= ?
                             and (decided_at is null or cast(decided_at as date) > ?))   as open_at_end_of_day
        from gold.fct_preauth_request
    """, [args.ds] * 6).fetchone()
    exceptions = con.execute("select sum(admissions), sum(paid_usd) from gold.rpt_preauth_controls where is_exception").fetchone()
    kpis = dict(zip(["submitted", "decided", "approved", "sla_missed", "open_at_end_of_day"], row))
    kpis.update(ds=args.ds, control_exception_admissions=exceptions[0], control_exception_paid_usd=float(exceptions[1] or 0))
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"{args.ds}.json").write_text(json.dumps(kpis, indent=1, default=str))
    print(json.dumps(kpis, default=str))


if __name__ == "__main__":
    main()
