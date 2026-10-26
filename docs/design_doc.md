# Design doc: Health Claims & Pre-Authorisation Warehouse

| | |
|---|---|
| **Author** | Stanley Igwe |
| **Status** | Core build complete on DE-SynPUF Sample 1 |
| **Last updated** | 2026-10-26 |

## 1. Problem and users
- **Users:** medical-operations managers, actuaries and finance at a health insurer; internal audit.
- **Questions they need answered:** How fast are pre-authorisations decided, and do we meet the regulator's deadlines? What does a member cost per month, by condition burden? Which admissions were paid without approval?
- **Current pain (scenario):** turnaround is measured from spreadsheets that count time waiting on providers against the insurer. PMPM uses today's member attributes for last year's claims. Analysts get raw member ids to "just check something".

## 2. Requirements
| Type | Requirement |
|---|---|
| Functional | Claim-line fact, pre-auth accumulating snapshot, SCD2 member history, PMPM, turnaround, control exceptions. |
| Data quality | Every claim line and cent reconciles to bronze; gaps against CMS's own totals are reported, not hidden. |
| Privacy | Raw identifiers and birth dates never leave bronze; a test enforces it on every build. |
| Freshness / SLA | Daily run, finished within 2 hours of being queued (Airflow Deadline Alert). |
| Scale | 857k claim lines build in 7.7 s on DuckDB; the same SQL runs on Postgres (and, via dbt adapters, on a cloud warehouse at 10x+). |

## 3. Design
- **Layers:** bronze (raw text, as delivered) → silver (typed, masked, SCD2 history) → gold (star schema and reports).
- **Key choices:** SCD2 built from yearly snapshots by hashing tracked attributes. Facts join on the member version valid on their date. Turnaround stops the clock while a request waits for information. Requests match admissions on member, provider and a ±3-day window, one-to-one. Dateless lines are quarantined, not dropped.

## 4. Options considered
| Decision | Options | Chosen | Why |
|---|---|---|---|
| Member history | Latest attributes only; dbt snapshot; SCD2 from yearly files | SCD2 from yearly files | The source is yearly snapshots; a dbt snapshot would only see the last load. |
| Early-arriving facts | Drop; "unknown member" row; extend first version back | Extend first version | Keeps 594 late-2007 lines ($3.1M) with the member's earliest known attributes. |
| Masking | Views with grants; tokenisation service; salted hash in staging | Salted hash in staging | Simple, joinable, and testable; a tokenisation vault is the production upgrade. |
| SLA in Airflow 3 | Task SLAs (removed in 3.0); Deadline Alerts | Deadline Alerts | The supported replacement; it fires on the run's wall-clock deadline. |
| Warehouse | Postgres only; DuckDB only; both | DuckDB locally, Postgres in CI | Fast local iteration; cross-database macros prove the SQL is portable. |

## 5. Risks and what I'd change at 10x scale
- Pre-authorisation events are synthetic. Turnaround and control figures prove the logic, not real operations.
- Claim matching on a ±3-day window can mis-pair repeat admissions; a real payer would carry the authorisation number on the claim.
- At 10x: incremental `fct_claim_line` by service month; snapshots of the accumulating fact for trend history; a tokenisation service with role-based unmasking; Postgres partitioning or a cloud warehouse.
