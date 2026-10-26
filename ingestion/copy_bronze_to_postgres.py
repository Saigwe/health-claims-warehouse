"""Copy the bronze tables from the DuckDB file into Postgres `bronze`, so the same dbt project builds on Postgres.

Column names are lower-cased on the way (Postgres folds unquoted names to lower case; DuckDB doesn't care).
Connection details come from the standard PG* environment variables.

Usage: python ingestion/copy_bronze_to_postgres.py --db warehouse/fixture.duckdb
"""
from __future__ import annotations

import argparse
import os

import duckdb

TABLES = ["beneficiary_summary", "inpatient_claims", "outpatient_claims", "preauth_events"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    args = ap.parse_args()
    dsn = " ".join(f"{k}={os.environ[v]}" for k, v in [("host", "PGHOST"), ("port", "PGPORT"), ("user", "PGUSER"),
                                                        ("password", "PGPASSWORD"), ("dbname", "PGDATABASE")] if v in os.environ)
    con = duckdb.connect(args.db, read_only=True)
    con.execute("install postgres; load postgres")
    con.execute(f"attach '{dsn}' as pg (type postgres)")
    con.execute("call postgres_execute('pg', 'create schema if not exists bronze')")
    for t in TABLES:
        cols = [r[0] for r in con.execute(f"describe bronze.{t}").fetchall()]
        select = ", ".join(f'"{c}" as "{c.lower()}"' for c in cols)
        con.execute(f"drop table if exists pg.bronze.{t}")
        con.execute(f"create table pg.bronze.{t} as select {select} from bronze.{t}")
        print(f"pg bronze.{t}: {con.execute(f'select count(*) from pg.bronze.{t}').fetchone()[0]:,} rows")


if __name__ == "__main__":
    main()
