select
    claim_id,
    member_id,
    provider_id,
    cast(service_date as date)              as service_date,
    paid_amount_usd
from {{ source('bronze', 'claims') }}
