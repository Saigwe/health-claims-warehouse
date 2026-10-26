# Ingestion

| Script | Writes | Notes |
|---|---|---|
| `load_synpuf.py` | `bronze.beneficiary_summary`, `bronze.inpatient_claims`, `bronze.outpatient_claims` | CMS DE-SynPUF Sample 1 as text. `--if-changed` skips the load when the files' MD5s match `bronze.load_log`. |
| `generate_preauth.py` | `data/synthetic/preauth_events.csv` | SYNTHETIC pre-authorisation events on top of the real admissions, fixed seed. |
| `load_preauth_events.py` | `bronze.preauth_events` | Delete + insert for a date range, so daily runs, retries and backfills are idempotent. |
| `copy_bronze_to_postgres.py` | Postgres `bronze.*` | For the Postgres CI job; lower-cases column names. |

Download (public, no sign-in): `make download`, or the files listed on the
[CMS DE-SynPUF page](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files).
