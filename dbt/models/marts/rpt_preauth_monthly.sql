select
    cast({{ dbt.date_trunc('month', 'requested_at') }} as date)                     as request_month,
    count(*)                                                                        as requests,
    1.0 * count(*) filter (where decision = 'approved')
        / nullif(count(*) filter (where decision <> 'pending'), 0)                 as approval_rate,
    median(turnaround_hours)                                                        as median_turnaround_hours
from {{ ref('fct_preauth_request') }}
group by 1
