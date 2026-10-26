"""Daily health-claims warehouse run (Airflow 3).

    check_sources -> load_claims_if_changed -> load_preauth_events[ds] -> dbt_build -> publish_kpis

- Idempotent per day: pre-authorisation events for the logical date are deleted and reinserted, claims reload only
  when the CMS files change, and dbt rebuilds from bronze. A retry or a backfill gives the same tables.
- Retries: 2 per task with exponential backoff; each task has an execution timeout.
- SLA: Airflow 3 replaced task SLAs with Deadline Alerts. The run must finish within 2 hours of being queued,
  or hcw_alerts.deadline_missed fires.
- Backfill:  airflow backfill create --dag-id health_claims_daily --from-date 2009-03-01 --to-date 2009-03-31

Configuration comes from environment variables, so the same DAG runs locally, in CI and in production:
  HCW_HOME (repo root), HCW_PYTHON and HCW_DBT (the project's own venv), HCW_DB (DuckDB file), HCW_RAW (CMS files),
  HCW_EVENTS (pre-authorisation event file).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG, DeadlineAlert, DeadlineReference, SyncCallback

ENV = "cd \"$HCW_HOME\" && "
default_args = {
    "owner": "data-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "execution_timeout": timedelta(minutes=30),
}

with DAG(
    dag_id="health_claims_daily",
    description="Load DE-SynPUF claims and the day's pre-authorisation events, then rebuild and test the warehouse.",
    schedule="@daily",
    start_date=datetime(2008, 1, 1),
    end_date=datetime(2010, 12, 31),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    deadline=DeadlineAlert(
        reference=DeadlineReference.DAGRUN_QUEUED_AT,
        interval=timedelta(hours=2),
        callback=SyncCallback("hcw_alerts.deadline_missed", kwargs={"dag_id": "health_claims_daily"}),
    ),
    tags=["health", "claims", "dbt"],
) as dag:
    check_sources = BashOperator(
        task_id="check_sources",
        bash_command=ENV + "ls \"$HCW_RAW\"/DE1_0_*_Sample_1.* > /dev/null && test -f \"$HCW_EVENTS\"",
        retries=0,
    )
    load_claims = BashOperator(
        task_id="load_claims_if_changed",
        bash_command=ENV + "\"$HCW_PYTHON\" ingestion/load_synpuf.py --raw \"$HCW_RAW\" --db \"$HCW_DB\" --if-changed",
    )
    load_events = BashOperator(
        task_id="load_preauth_events",
        bash_command=ENV + "\"$HCW_PYTHON\" ingestion/load_preauth_events.py --db \"$HCW_DB\" --events \"$HCW_EVENTS\" --start {{ ds }} --end {{ ds }}",
    )
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=ENV + "cd dbt && DUCKDB_PATH=\"$HCW_DB\" \"$HCW_DBT\" build --profiles-dir .",
        execution_timeout=timedelta(minutes=45),
    )
    publish = BashOperator(
        task_id="publish_kpis",
        bash_command=ENV + "\"$HCW_PYTHON\" analysis/daily_kpis.py --db \"$HCW_DB\" --ds {{ ds }} --out results/daily",
    )

    check_sources >> load_claims >> load_events >> dbt_build >> publish
