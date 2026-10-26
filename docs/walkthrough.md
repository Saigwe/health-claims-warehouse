# 3-minute walkthrough: Health Claims & Pre-Authorisation Warehouse

A timed script for a Loom recording of about 3 minutes (screen plus camera bubble, 1080p). Say it in your own words; the lines are a guide, not a teleprompter.

**Open these tabs before you press record:** README, dbt/models, airflow/dags, docs/design_doc.md, GitHub Actions (DuckDB, Postgres, Airflow).

| Time | On screen | What to say |
|---|---|---|
| 0:00–0:20 | Portfolio card, then the README title | Medical-operations teams need pre-authorisation turnaround, cost per member, and admissions paid without approval, without anyone seeing an identifiable member. This Kimball warehouse covers 857k CMS synthetic claim lines. |
| 0:20–0:45 | README intro and the Data section | At a Big Four firm I delivered a data warehouse and medical-operations dashboards for a health insurer, covering about 800k pre-authorisation requests. This rebuilds it on CMS's public synthetic Medicare data. No client data is used. |
| 0:45–1:10 | The star-schema diagram in the README | Member history is SCD2, built from yearly files. That's 279,711 versions, and claims join the version valid on their service date. |
| 1:10–1:35 | `fct_preauth_request`, the accumulating snapshot | The clock stops while a request waits for information. Turnaround is checked against CMS's 72-hour and 7-day deadlines. |
| 1:35–2:00 | The masking test and the Airflow DAG | Identifiers are hashed at the first layer, and a test fails the build if one leaks. The Airflow 3 DAG is idempotent. |
| 2:00–2:30 | Numbers: PMPM and the reconciliation to CMS totals | In 2008, inpatient cost was $2.67 per member per month with no chronic conditions, against $759 with five or more. I report the gap to CMS's own totals instead of forcing a match. |
| 2:30–2:45 | `docs/design_doc.md`, the options table | The decision I'd defend in an interview: Privacy enforced by the pipeline, not a policy document: the build fails if a raw identifier reaches silver or gold. |
| 2:45–3:00 | Back to the README top | For an insurer, that means one trusted cost and turnaround view, and leakage found from the data, not from audit sampling. The repo, numbers and design doc are linked under the video. |

## Recording checklist
- Close email, chat and notifications. Zoom the browser to 125% so code is readable.
- Run `make fixture-all` once before recording, so CI-style output is fresh if you show it.
- Keep to one take per section; Loom lets you trim. Aim for 2:45 to 3:10.
- Show real numbers on screen as you say them; never estimate on camera.
- Say "synthetic" out loud wherever the README labels data as synthetic.

## After recording
1. Copy the Loom share link.
2. In `README.md`, replace the roadmap line with `- [x] [3-minute Loom walkthrough](<your Loom link>)` and add the link under the title.
3. Add the link to this project's card on saigwe.github.io.
