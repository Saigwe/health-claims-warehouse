-- Provider dimension (DE-SynPUF institutional provider numbers).
select
    provider_id,
    min(service_from_date)                                          as first_claim_date,
    max(service_from_date)                                          as last_claim_date,
    count(distinct case when setting = 'inpatient' then claim_id end) as inpatient_claims,
    count(distinct case when setting = 'outpatient' then claim_id end) as outpatient_claims
from {{ ref('stg_synpuf__claim_lines') }}
where provider_id is not null
group by 1
