"""Synthetic CSVs in the exact DE-SynPUF Sample 1 file names and columns, so CI runs the real loader, the
pre-authorisation generator and dbt unchanged. Includes the awkward cases found in the real files: claims
dated before the first enrolment year, and a segment 2 whose segment 1 is missing.

Usage: python tests/fixtures/make_fixture.py --raw data/fixture/raw
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

N_MEMBERS, N_IP, N_OP = 1_500, 900, 6_000
CHRONIC = ["SP_ALZHDMTA", "SP_CHF", "SP_CHRNKIDN", "SP_CNCR", "SP_COPD", "SP_DEPRESSN", "SP_DIABETES", "SP_ISCHMCHT",
           "SP_OSTEOPRS", "SP_RA_OA", "SP_STRKETIA"]


def ymd(d) -> pd.Series:
    return pd.Series(pd.to_datetime(d)).dt.strftime("%Y%m%d")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=Path("data/fixture/raw"))
    args = ap.parse_args()
    args.raw.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(1313)
    ids = [f"{i:016X}" for i in rng.choice(16**12, N_MEMBERS, replace=False)]
    birth = ymd(pd.Timestamp("1915-01-01") + pd.to_timedelta(rng.integers(0, 365 * 60, N_MEMBERS), unit="D"))
    flags = rng.random((N_MEMBERS, len(CHRONIC))) < 0.3
    for year in (2008, 2009, 2010):
        flags = flags | (rng.random(flags.shape) < 0.05)  # conditions accrue: SCD2 versions
        df = pd.DataFrame({
            "DESYNPUF_ID": ids, "BENE_BIRTH_DT": birth, "BENE_DEATH_DT": None,
            "BENE_SEX_IDENT_CD": rng.choice(["1", "2"], N_MEMBERS), "BENE_RACE_CD": rng.choice(["1", "2", "3", "5"], N_MEMBERS),
            "BENE_ESRD_IND": rng.choice(["0", "Y"], N_MEMBERS, p=[0.95, 0.05]),
            "SP_STATE_CODE": [str(s) for s in rng.integers(1, 54, N_MEMBERS)],
            "BENE_COUNTY_CD": [str(c) for c in rng.integers(1, 900, N_MEMBERS)],
            "BENE_HI_CVRAGE_TOT_MONS": "12", "BENE_SMI_CVRAGE_TOT_MONS": rng.choice(["12", "0"], N_MEMBERS, p=[0.9, 0.1]),
            "BENE_HMO_CVRAGE_TOT_MONS": "0", "PLAN_CVRG_MOS_NUM": "12",
            **{c: np.where(flags[:, i], "1", "2") for i, c in enumerate(CHRONIC)},
            "MEDREIMB_IP": (rng.integers(0, 3, N_MEMBERS) * 5000).astype(str),
            "MEDREIMB_OP": (rng.integers(0, 10, N_MEMBERS) * 100).astype(str),
        })
        df.to_csv(args.raw / f"DE1_0_{year}_Beneficiary_Summary_File_Sample_1.csv", index=False)

    providers = [f"{p:04d}AB" for p in range(60)]
    adm = pd.Timestamp("2007-12-01") + pd.to_timedelta(rng.integers(0, 1125, N_IP), unit="D")
    los = rng.integers(1, 10, N_IP)
    ip = pd.DataFrame({
        "DESYNPUF_ID": rng.choice(ids, N_IP), "CLM_ID": [f"9{i:014d}" for i in range(N_IP)], "SEGMENT": "1",
        "CLM_FROM_DT": ymd(adm), "CLM_THRU_DT": ymd(adm + pd.to_timedelta(los, unit="D")),
        "PRVDR_NUM": rng.choice(providers, N_IP), "CLM_PMT_AMT": (rng.integers(1, 30, N_IP) * 1000).astype(str),
        "NCH_PRMRY_PYR_CLM_PD_AMT": "0", "AT_PHYSN_NPI": [str(n) for n in rng.integers(10**9, 10**10, N_IP)],
        "ICD9_DGNS_CD_1": "4280", "ICD9_PRCDR_CD_1": None, "CLM_ADMSN_DT": ymd(adm),
        "NCH_BENE_DSCHRG_DT": ymd(adm + pd.to_timedelta(los, unit="D")), "CLM_UTLZTN_DAY_CNT": los.astype(str),
        "CLM_DRG_CD": rng.choice(["882", "177", "886", "190"], N_IP), "NCH_BENE_IP_DDCTBL_AMT": "1068",
        "NCH_BENE_PTA_COINSRNC_LBLTY_AM": "0",
    })
    ip.to_csv(args.raw / "DE1_0_2008_to_2010_Inpatient_Claims_Sample_1.csv", index=False)

    svc = pd.Timestamp("2008-01-01") + pd.to_timedelta(rng.integers(0, 1095, N_OP), unit="D")
    op = pd.DataFrame({
        "DESYNPUF_ID": rng.choice(ids, N_OP), "CLM_ID": [f"5{i:014d}" for i in range(N_OP)], "SEGMENT": "1",
        "CLM_FROM_DT": ymd(svc), "CLM_THRU_DT": ymd(svc), "PRVDR_NUM": rng.choice(providers, N_OP),
        "CLM_PMT_AMT": (rng.integers(1, 30, N_OP) * 10).astype(str), "NCH_PRMRY_PYR_CLM_PD_AMT": "0",
        "AT_PHYSN_NPI": None, "ICD9_DGNS_CD_1": "V5869", "ICD9_PRCDR_CD_1": None, "NCH_BENE_PTB_DDCTBL_AMT": "0",
        "NCH_BENE_PTB_COINSRNC_AMT": "10", "HCPCS_CD_1": "99213",
    })
    op.loc[: 9, ["SEGMENT", "CLM_FROM_DT", "CLM_THRU_DT"]] = ["2", None, None]  # segment 2 with no segment 1
    op.to_csv(args.raw / "DE1_0_2008_to_2010_Outpatient_Claims_Sample_1.csv", index=False)
    print(f"wrote SynPUF-format fixture CSVs to {args.raw}")


if __name__ == "__main__":
    main()
