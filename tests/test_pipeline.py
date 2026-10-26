"""Pipeline tests on a built warehouse (HCW_DB, the CI fixture by default):
  - the masking-policy test fails when a raw identifier leaks into gold (so it is really testing something)
  - the daily pre-authorisation load is idempotent: re-running a day changes nothing
"""
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys

import duckdb
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = pathlib.Path(os.environ.get("HCW_DB", ROOT / "warehouse" / "fixture.duckdb")).resolve()
EVENTS = pathlib.Path(os.environ.get("HCW_EVENTS", ROOT / "data" / "fixture" / "preauth_events.csv")).resolve()


def dbt(*args: str) -> int:
    """Run dbt in its own process, so it never holds the DuckDB file open in this one."""
    exe = shutil.which("dbt", path=str(pathlib.Path(sys.executable).parent)) or "dbt"
    env = {**os.environ, "DUCKDB_PATH": str(DB)}
    return subprocess.run([exe, *args, "--profiles-dir", ".", "--quiet"], cwd=ROOT / "dbt", env=env,
                          capture_output=True).returncode


@pytest.fixture
def leaked_view():
    with duckdb.connect(str(DB)) as con:
        con.execute("create or replace view gold.leaky_export as "
                    "select DESYNPUF_ID as member_id, BENE_BIRTH_DT from bronze.beneficiary_summary")
    yield
    with duckdb.connect(str(DB)) as con:
        con.execute("drop view if exists gold.leaky_export")


def test_masking_policy_passes_on_the_warehouse():
    assert dbt("test", "--select", "assert_pii_masking_policy") == 0


def test_masking_policy_catches_a_leak(leaked_view):
    assert dbt("test", "--select", "assert_pii_masking_policy") == 1


def test_daily_preauth_load_is_idempotent():
    with duckdb.connect(str(DB), read_only=True) as con:
        day = str(con.execute("select cast(min(event_at) as date) + 30 from bronze.preauth_events").fetchone()[0])
        before = con.execute("select count(*), count(distinct event_id) from bronze.preauth_events").fetchone()
    cmd = [sys.executable, "ingestion/load_preauth_events.py", "--db", str(DB), "--events", str(EVENTS),
           "--start", day, "--end", day]
    for _ in range(2):
        subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True)
    with duckdb.connect(str(DB), read_only=True) as con:
        after = con.execute("select count(*), count(distinct event_id) from bronze.preauth_events").fetchone()
    assert before == after and after[0] == after[1]
