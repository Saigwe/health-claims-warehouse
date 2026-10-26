"""Load CMS DE-SynPUF Sample 1 (synthetic Medicare data, no real patients) into DuckDB `bronze`.

    bronze.beneficiary_summary   one row per beneficiary per year (2008, 2009, 2010), all 32 columns + file_year
    bronze.inpatient_claims      2008-2010 inpatient claims (one row per claim segment), the columns we model
    bronze.outpatient_claims     2008-2010 outpatient claims, the columns we model

Everything lands as text, exactly as delivered; typing, masking and dedup happen in dbt staging.
Source (public, no sign-in):
https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files

The files are yearly deliveries, so the daily DAG runs this with --if-changed: it hashes the CSVs and skips
the load when they match bronze.load_log.

Usage
    python ingestion/load_synpuf.py --raw data/raw --db warehouse/claims.duckdb [--if-changed]
"""
from __future__ import annotations

import argparse
import hashlib
import time
import zipfile
from pathlib import Path

import duckdb

CLAIM_COLUMNS = [
    "DESYNPUF_ID", "CLM_ID", "SEGMENT", "CLM_FROM_DT", "CLM_THRU_DT", "PRVDR_NUM", "CLM_PMT_AMT",
    "NCH_PRMRY_PYR_CLM_PD_AMT", "AT_PHYSN_NPI", "ICD9_DGNS_CD_1", "ICD9_PRCDR_CD_1",
]
INPATIENT_ONLY = ["CLM_ADMSN_DT", "NCH_BENE_DSCHRG_DT", "CLM_UTLZTN_DAY_CNT", "CLM_DRG_CD", "NCH_BENE_IP_DDCTBL_AMT",
                  "NCH_BENE_PTA_COINSRNC_LBLTY_AM"]
OUTPATIENT_ONLY = ["NCH_BENE_PTB_DDCTBL_AMT", "NCH_BENE_PTB_COINSRNC_AMT", "HCPCS_CD_1"]


def csv_for(raw: Path, stem: str) -> Path:
    csv = raw / f"{stem}.csv"
    if not csv.exists():
        with zipfile.ZipFile(raw / f"{stem}.zip") as z:
            z.extract(f"{stem}.csv", raw)
    return csv


STEMS = [f"DE1_0_{y}_Beneficiary_Summary_File_Sample_1" for y in (2008, 2009, 2010)] + [
    f"DE1_0_2008_to_2010_{s}_Claims_Sample_1" for s in ("Inpatient", "Outpatient")]


def file_md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", type=Path, default=Path("data/raw"))
    ap.add_argument("--db", default="warehouse/claims.duckdb")
    ap.add_argument("--if-changed", action="store_true", help="skip when the files match the last load")
    args = ap.parse_args()

    start = time.time()
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(args.db)
    con.execute("create schema if not exists bronze")
    con.execute("create table if not exists bronze.load_log (file varchar, md5 varchar, loaded_at timestamp)")
    hashes = {stem: file_md5(csv_for(args.raw, stem)) for stem in STEMS}
    last = dict(con.execute("select file, arg_max(md5, loaded_at) from bronze.load_log group by 1").fetchall())
    if args.if_changed and last == hashes:
        print("source files unchanged since the last load: skipped")
        return
    years = []
    for year in (2008, 2009, 2010):
        path = csv_for(args.raw, f"DE1_0_{year}_Beneficiary_Summary_File_Sample_1").as_posix()
        years.append(f"select *, '{year}' as file_year from read_csv('{path}', all_varchar = true)")
    con.execute("create or replace table bronze.beneficiary_summary as " + " union all by name ".join(years))
    for setting, extra in (("inpatient", INPATIENT_ONLY), ("outpatient", OUTPATIENT_ONLY)):
        path = csv_for(args.raw, f"DE1_0_2008_to_2010_{setting.capitalize()}_Claims_Sample_1").as_posix()
        con.execute(f"create or replace table bronze.{setting}_claims as "
                    f"select {', '.join(CLAIM_COLUMNS + extra)} from read_csv('{path}', all_varchar = true)")
    con.executemany("insert into bronze.load_log values (?, ?, current_timestamp)", list(hashes.items()))
    for t in ("beneficiary_summary", "inpatient_claims", "outpatient_claims"):
        print(f"bronze.{t:<20} {con.execute(f'select count(*) from bronze.{t}').fetchone()[0]:>9,} rows")
    print(f"loaded in {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
