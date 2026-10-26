PY ?= python
DB ?= warehouse/claims.duckdb
RAW ?= data/raw
EVENTS ?= data/synthetic/preauth_events.csv
DBT_BIN ?= dbt
DBT = cd dbt && DUCKDB_PATH=../$(DB) $(DBT_BIN)
CMS = https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/SynPUFs/Downloads

.PHONY: all download load preauth dbt test fixture-all fixture postgres-fixture clean

all: load preauth dbt test   ## real CMS DE-SynPUF Sample 1 (run `make download` once first)

download:   ## ~49 MB of zips from cms.gov, no sign-in
	mkdir -p $(RAW)
	for f in DE1_0_2008_Beneficiary_Summary_File_Sample_1 DE1_0_2009_Beneficiary_Summary_File_Sample_1 \
	         DE1_0_2008_to_2010_Inpatient_Claims_Sample_1 DE1_0_2008_to_2010_Outpatient_Claims_Sample_1; do \
	  curl -L -o $(RAW)/$$f.zip $(CMS)/$$f.zip; done
	curl -L -o $(RAW)/DE1_0_2010_Beneficiary_Summary_File_Sample_1.zip \
	  https://www.cms.gov/sites/default/files/2020-09/DE1_0_2010_Beneficiary_Summary_File_Sample_1.zip

load:
	$(PY) ingestion/load_synpuf.py --raw $(RAW) --db $(DB)

preauth:
	$(PY) ingestion/generate_preauth.py --db $(DB) --out $(EVENTS)
	$(PY) ingestion/load_preauth_events.py --db $(DB) --events $(EVENTS) --all

dbt:
	$(DBT) deps --profiles-dir . && $(DBT) build --profiles-dir .

test:
	HCW_DB=$(DB) HCW_EVENTS=$(EVENTS) $(PY) -m pytest -q tests

fixture-all:   ## synthetic SynPUF-format files through the real loaders, dbt and tests (CI)
	$(PY) tests/fixtures/make_fixture.py --raw data/fixture/raw
	$(MAKE) load preauth dbt test DB=warehouse/fixture.duckdb RAW=data/fixture/raw EVENTS=data/fixture/preauth_events.csv

postgres-fixture: fixture-all   ## then the same dbt project on Postgres (PG* env vars)
	$(PY) ingestion/copy_bronze_to_postgres.py --db warehouse/fixture.duckdb
	cd dbt && DBT_TARGET=postgres $(DBT_BIN) build --profiles-dir .

clean:
	rm -rf warehouse dbt/target dbt/logs data/fixture
