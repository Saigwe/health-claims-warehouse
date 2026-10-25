select
    request_id,
    member_id,
    provider_id,
    requested_at,
    decision,
    decided_at,
    requested_amount_usd
from {{ source('bronze', 'preauth_requests') }}
