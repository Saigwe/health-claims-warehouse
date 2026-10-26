"""SYNTHETIC pre-authorisation events, generated on top of the real DE-SynPUF inpatient admissions.

DE-SynPUF has claims but no pre-authorisation workflow, so this script writes one, deterministically (fixed seed):
  - 95% of admissions get a request that is approved before admission (25% after a request for information)
  - 2% get a request that was DENIED, yet the claim was paid       -> a control exception
  - 3% get no request at all                                         -> a control exception
  - extra requests with no admission: denied, withdrawn, or still open at the end of the data
Requests carry member, provider, planned admission date and DRG, not a claim id: the warehouse has to match
requests to claims the way a payer does (same member and provider, admission within 3 days of the plan).

Output: an event log (one row per state change), data/synthetic/preauth_events.csv
Usage:  python ingestion/generate_preauth.py --db warehouse/claims.duckdb --out data/synthetic/preauth_events.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

SEED = 1313


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default="warehouse/claims.duckdb")
    ap.add_argument("--out", type=Path, default=Path("data/synthetic/preauth_events.csv"))
    args = ap.parse_args()
    rng = np.random.default_rng(SEED)
    con = duckdb.connect(args.db, read_only=True)
    adm = con.execute("""
        select DESYNPUF_ID as member_id, PRVDR_NUM as provider_num, CLM_DRG_CD as drg,
               strptime(coalesce(CLM_ADMSN_DT, CLM_FROM_DT), '%Y%m%d') as admission_at
        from bronze.inpatient_claims
        where SEGMENT = '1' and coalesce(CLM_ADMSN_DT, CLM_FROM_DT) is not null
        order by CLM_ID
    """).df()
    members = con.execute("select distinct DESYNPUF_ID from bronze.beneficiary_summary order by 1").df().DESYNPUF_ID.to_numpy()
    providers = adm.provider_num.unique()

    n = len(adm)
    cohort = rng.choice(["approved", "denied_paid", "none"], n, p=[0.95, 0.02, 0.03])
    req = adm[cohort != "none"].assign(outcome=np.where(cohort[cohort != "none"] == "approved", "approved", "denied"))

    n_extra = int(n * 0.10)
    planned = pd.Timestamp("2008-01-01") + pd.to_timedelta(rng.integers(0, 1095, n_extra), unit="D")
    extra = pd.DataFrame({
        "member_id": rng.choice(members, n_extra), "provider_num": rng.choice(providers, n_extra),
        "drg": rng.choice(adm.drg.dropna().to_numpy(), n_extra), "admission_at": planned,
        "outcome": rng.choice(["denied", "withdrawn"], n_extra, p=[0.7, 0.3])})
    extra.loc[extra.admission_at >= "2010-12-24", "outcome"] = "open"
    req = pd.concat([req, extra], ignore_index=True)

    m = len(req)
    req["request_id"] = [f"PA{i:07d}" for i in range(m)]
    req["priority"] = rng.choice(["urgent", "standard"], m, p=[0.2, 0.8])
    urgent = req.priority.eq("urgent").to_numpy()
    lead_days = np.where(urgent, rng.integers(0, 2, m), rng.integers(3, 22, m))
    hour = rng.integers(8, 18, m)
    submitted = req.admission_at - pd.to_timedelta(lead_days, unit="D") + pd.to_timedelta(hour, unit="h")
    info = rng.random(m) < 0.25
    info_req = submitted + pd.to_timedelta(rng.lognormal(2.0, 0.7, m), unit="h")
    info_rec = info_req + pd.to_timedelta(rng.lognormal(3.2, 0.9, m), unit="h")
    base = np.where(info, info_rec, submitted)
    decide_hours = np.where(urgent, rng.lognormal(2.0, 0.6, m), rng.lognormal(3.3, 0.7, m))
    decided = pd.to_datetime(base) + pd.to_timedelta(decide_hours, unit="h")

    ev = [pd.DataFrame({"request_id": req.request_id, "event_type": "submitted", "event_at": submitted})]
    ev.append(pd.DataFrame({"request_id": req.request_id[info], "event_type": "info_requested", "event_at": info_req[info]}))
    ev.append(pd.DataFrame({"request_id": req.request_id[info], "event_type": "info_received", "event_at": info_rec[info]}))
    closed = req.outcome.ne("open").to_numpy()
    ev.append(pd.DataFrame({"request_id": req.request_id[closed], "event_type": req.outcome[closed],
                            "event_at": decided[closed]}))
    events = pd.concat(ev, ignore_index=True).merge(
        req[["request_id", "member_id", "provider_num", "drg", "priority", "admission_at"]], on="request_id")
    events = events.rename(columns={"admission_at": "planned_admission_date"}).sort_values(["event_at", "request_id"])
    events["event_id"] = [f"EV{i:08d}" for i in range(len(events))]
    events["planned_admission_date"] = events.planned_admission_date.dt.date
    events["event_at"] = events.event_at.dt.floor("s")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["event_id", "request_id", "event_type", "event_at", "member_id", "provider_num", "priority", "drg",
            "planned_admission_date"]
    events[cols].to_csv(args.out, index=False)
    print(f"{m:,} synthetic requests, {len(events):,} events -> {args.out}")


if __name__ == "__main__":
    main()
