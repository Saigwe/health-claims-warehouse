-- Claims paid vs the beneficiary summary file's reimbursement totals, by year and setting. The two are separate
-- CMS deliverables; the gap is a data-quality finding to report, not a modelling error to hide.
with claims as (
    select service_year as year, setting, sum(paid_usd) as claims_paid_usd
    from {{ ref('fct_claim_line') }}
    group by 1, 2
),
summary as (
    select file_year as year, 'inpatient' as setting, sum(summary_inpatient_paid_usd) as summary_paid_usd
    from {{ ref('stg_synpuf__beneficiary_years') }} group by 1
    union all
    select file_year, 'outpatient', sum(summary_outpatient_paid_usd)
    from {{ ref('stg_synpuf__beneficiary_years') }} group by 1
)
select
    s.year,
    s.setting,
    coalesce(c.claims_paid_usd, 0)                                  as claims_paid_usd,
    s.summary_paid_usd,
    coalesce(c.claims_paid_usd, 0) - s.summary_paid_usd             as gap_usd,
    (coalesce(c.claims_paid_usd, 0) - s.summary_paid_usd) / nullif(s.summary_paid_usd, 0) as gap_share
from summary s
left join claims c on c.year = s.year and c.setting = s.setting
