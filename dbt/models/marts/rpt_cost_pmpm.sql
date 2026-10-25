-- Paid claims per member per month (all members treated as enrolled all period in the fixture).
with members as (select count(*) as members from {{ ref('stg_bronze__members') }})
select
    cast({{ dbt.date_trunc('month', 'service_date') }} as date)    as service_month,
    sum(paid_amount_usd)                                           as paid_usd,
    sum(paid_amount_usd) / max(m.members)                          as paid_pmpm_usd
from {{ ref('stg_bronze__claims') }}
cross join members m
group by 1
