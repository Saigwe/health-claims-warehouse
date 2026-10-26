-- Paid claims per member per month (PMPM) by year, setting and chronic-condition burden. Member months come
-- from each member's Part A coverage months for inpatient and Part B months for outpatient, and claims count
-- in the member's chronic-condition band for that year (point-in-time, via member_sk).
with exposure as (
    select
        y.file_year                                                 as year,
        m.chronic_condition_count,
        sum(y.part_a_months)                                        as part_a_member_months,
        sum(y.part_b_months)                                        as part_b_member_months
    from {{ ref('stg_synpuf__beneficiary_years') }} y
    join {{ ref('dim_member') }} m
      on m.member_key = y.member_key and cast(cast(y.file_year as varchar) || '-07-01' as date) between m.valid_from and m.valid_to
    group by 1, 2
),
banded as (
    select year, case when chronic_condition_count = 0 then '0' when chronic_condition_count <= 2 then '1-2'
                      when chronic_condition_count <= 4 then '3-4' else '5+' end as chronic_band,
           sum(part_a_member_months) as part_a_member_months, sum(part_b_member_months) as part_b_member_months
    from exposure group by 1, 2
),
paid as (
    select
        f.service_year                                              as year,
        case when m.chronic_condition_count = 0 then '0' when m.chronic_condition_count <= 2 then '1-2'
             when m.chronic_condition_count <= 4 then '3-4' else '5+' end as chronic_band,
        sum(f.paid_usd) filter (where f.setting = 'inpatient')      as inpatient_paid_usd,
        sum(f.paid_usd) filter (where f.setting = 'outpatient')     as outpatient_paid_usd
    from {{ ref('fct_claim_line') }} f
    join {{ ref('dim_member') }} m on m.member_sk = f.member_sk
    group by 1, 2
)
select
    b.year,
    b.chronic_band,
    b.part_a_member_months,
    b.part_b_member_months,
    coalesce(p.inpatient_paid_usd, 0)                               as inpatient_paid_usd,
    coalesce(p.outpatient_paid_usd, 0)                              as outpatient_paid_usd,
    coalesce(p.inpatient_paid_usd, 0) / nullif(b.part_a_member_months, 0) as inpatient_pmpm_usd,
    coalesce(p.outpatient_paid_usd, 0) / nullif(b.part_b_member_months, 0) as outpatient_pmpm_usd
from banded b
left join paid p on p.year = b.year and p.chronic_band = b.chronic_band
