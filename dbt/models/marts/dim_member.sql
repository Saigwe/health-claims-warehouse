-- Member dimension, SCD Type 2: one row per member per version, valid from 1 January of its first year to the
-- day before the next version starts. Facts join on the version valid on their service date. The first version
-- also covers any earlier date, so early-arriving facts (claims from late 2007, before the first enrolment
-- file) take the earliest known attributes instead of losing their member.
with h as (
    select
        *,
        case when version = 1 then cast('1900-01-01' as date)
             else cast(cast(first_year as varchar) || '-01-01' as date) end as valid_from,
        lead(first_year) over (partition by member_key order by version) as next_first_year
    from {{ ref('int_member_history') }}
)
select
    md5(member_key || '-' || cast(version as varchar))             as member_sk,
    member_key,
    version,
    valid_from,
    case when next_first_year is null then cast('9999-12-31' as date)
         else cast(cast(next_first_year as varchar) || '-01-01' as date) - 1 end as valid_to,
    next_first_year is null                                         as is_current,
    birth_year,
    sex,
    race,
    state_code,
    county_code,
    has_esrd,
    death_date,
    (case when has_alzheimers then 1 else 0 end + case when has_heart_failure then 1 else 0 end
     + case when has_kidney_disease then 1 else 0 end + case when has_cancer then 1 else 0 end
     + case when has_copd then 1 else 0 end + case when has_depression then 1 else 0 end
     + case when has_diabetes then 1 else 0 end + case when has_ischemic_heart_disease then 1 else 0 end
     + case when has_osteoporosis then 1 else 0 end + case when has_arthritis then 1 else 0 end
     + case when has_stroke_tia then 1 else 0 end)                 as chronic_condition_count,
    has_heart_failure,
    has_diabetes,
    has_kidney_disease,
    has_copd,
    has_cancer
from h
