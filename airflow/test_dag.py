"""DAG integrity tests, run in the Airflow CI job: it imports, runs in order, retries, and has a deadline."""
from __future__ import annotations

import pathlib

from airflow.dag_processing.dagbag import DagBag

DAGS = pathlib.Path(__file__).parent / "dags"


def load():
    bag = DagBag(dag_folder=str(DAGS), include_examples=False)
    assert not bag.import_errors, bag.import_errors
    return bag.get_dag("health_claims_daily")


def test_dag_order_and_policies():
    dag = load()
    order = ["check_sources", "load_claims_if_changed", "load_preauth_events", "dbt_build", "publish_kpis"]
    assert [t.task_id for t in dag.topological_sort()] == order
    for task in dag.tasks:
        if task.task_id != "check_sources":
            assert task.retries == 2 and task.execution_timeout is not None
    assert dag.max_active_runs == 1 and not dag.catchup
    assert dag.deadline, "the run needs a deadline alert (Airflow 3's replacement for SLAs)"


def test_daily_load_is_scoped_to_the_logical_date():
    dag = load()
    command = dag.get_task("load_preauth_events").bash_command
    assert "--start {{ ds }} --end {{ ds }}" in command
