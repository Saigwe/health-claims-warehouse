"""Load pre-authorisation events into `bronze.preauth_events` for a date range, idempotently.

The daily Airflow run calls this with --start = --end = the run's logical date. It deletes that day's events
and inserts them again, so a retry or a backfill over any range gives the same table, never duplicates.

Usage
    python ingestion/load_preauth_events.py --db warehouse/claims.duckdb --start 2009-03-01 --end 2009-03-01
    python ingestion/load_preauth_events.py --db warehouse/claims.duckdb --all
"""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default="warehouse/claims.duckdb")
    ap.add_argument("--events", type=Path, default=Path("data/synthetic/preauth_events.csv"))
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    if not args.all and not (args.start and args.end):
        ap.error("give --start and --end, or --all")
    start, end = ("0001-01-01", "9999-12-31") if args.all else (args.start, args.end)

    con = duckdb.connect(args.db)
    con.execute("create schema if not exists bronze")
    con.execute("""create table if not exists bronze.preauth_events (
        event_id varchar, request_id varchar, event_type varchar, event_at varchar, member_id varchar,
        provider_num varchar, priority varchar, drg varchar, planned_admission_date varchar, loaded_for date)""")
    con.execute("begin")
    con.execute("delete from bronze.preauth_events where cast(event_at as date) between ? and ?", [start, end])
    con.execute(f"""
        insert into bronze.preauth_events
        select *, cast(event_at as date) from read_csv('{args.events.as_posix()}', all_varchar = true)
        where cast(event_at as date) between ? and ?""", [start, end])
    con.execute("commit")
    n = con.execute("select count(*) from bronze.preauth_events where cast(event_at as date) between ? and ?",
                    [start, end]).fetchone()[0]
    total = con.execute("select count(*) from bronze.preauth_events").fetchone()[0]
    print(f"bronze.preauth_events: {n:,} events for {start}..{end} (table now {total:,})")


if __name__ == "__main__":
    main()
