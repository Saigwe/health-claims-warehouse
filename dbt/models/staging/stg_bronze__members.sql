-- PII: date of birth is reduced to birth year here; nothing downstream sees the full date.
select
    member_id,
    plan,
    extract(year from cast(date_of_birth as date)) as birth_year
from {{ source('bronze', 'members') }}
