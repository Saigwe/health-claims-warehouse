-- Accumulating snapshot: one row per pre-authorisation request, updated as it moves to a decision.
select
    r.request_id,
    r.member_id,
    r.provider_id,
    p.specialty,
    r.requested_at,
    r.decided_at,
    r.decision,
    r.requested_amount_usd,
    {{ dbt.datediff('r.requested_at', 'r.decided_at', 'minute') }} / 60.0 as turnaround_hours
from {{ ref('stg_bronze__preauth_requests') }} r
join {{ ref('stg_bronze__providers') }} p on p.provider_id = r.provider_id
