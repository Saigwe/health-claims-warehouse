-- One row per claim segment. member_sk is the member version valid on the service date (point-in-time join),
-- so a 2009 claim reports the member's 2009 chronic conditions, not today's. Lines with no service date are
-- quarantined in qa_claim_lines_without_dates instead.
select
    c.claim_line_id,
    c.claim_id,
    c.segment,
    c.setting,
    m.member_sk,
    c.member_key,
    c.provider_id,
    c.service_from_date,
    c.service_thru_date,
    c.admission_date,
    extract(year from c.service_from_date)                          as service_year,
    c.paid_usd,
    c.other_payer_paid_usd,
    c.deductible_usd,
    c.coinsurance_usd,
    c.utilization_days,
    c.drg_code,
    c.primary_diagnosis_code
from {{ ref('stg_synpuf__claim_lines') }} c
left join {{ ref('dim_member') }} m
    on m.member_key = c.member_key
   and c.service_from_date between m.valid_from and m.valid_to
where c.service_from_date is not null
