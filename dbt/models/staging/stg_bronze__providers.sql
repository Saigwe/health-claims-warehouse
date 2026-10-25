select
    provider_id,
    specialty
from {{ source('bronze', 'providers') }}
