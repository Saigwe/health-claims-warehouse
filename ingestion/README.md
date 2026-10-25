# Ingestion (roadmap)

Loaders for the real data go here and write to the same `bronze` tables as the fixture.

Real data: [Synthea](https://synthea.mitre.org/) synthetic patients or [CMS DE-SynPUF](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files) synthetic claims (no real patients). Generate pre-authorisation requests on top. CI uses a synthetic members, providers, requests and claims fixture.
