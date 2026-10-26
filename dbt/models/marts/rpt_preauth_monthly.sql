-- Medical-operations view of pre-authorisation, by month of submission and priority.
select
    cast(date_trunc('month', submitted_at) as date)                 as submitted_month,
    priority,
    count(*)                                                        as requests,
    count(decided_at)                                               as decided,
    count(*) filter (where status = 'approved')                     as approved,
    count(*) filter (where status = 'denied')                       as denied,
    count(*) filter (where status = 'approved') * 1.0
        / nullif(count(*) filter (where status in ('approved', 'denied')), 0) as approval_rate,
    count(*) filter (where was_pended) * 1.0 / count(*)             as pended_share,
    percentile_cont(0.5) within group (order by turnaround_hours)   as median_turnaround_hours,
    percentile_cont(0.9) within group (order by turnaround_hours)   as p90_turnaround_hours,
    count(*) filter (where met_sla) * 1.0 / nullif(count(decided_at), 0) as sla_met_share
from {{ ref('fct_preauth_request') }}
group by 1, 2
