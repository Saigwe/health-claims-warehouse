-- SYNTHETIC pre-authorisation event log (ingestion/generate_preauth.py). Member ids are masked like claims,
-- so requests and claims join on the same hashed key.
select
    event_id,
    request_id,
    event_type,
    cast(event_at as timestamp)                                     as event_at,
    {{ mask_id('member_id') }}                                      as member_key,
    provider_num                                                    as provider_id,
    priority,
    drg                                                             as drg_code,
    cast(planned_admission_date as date)                            as planned_admission_date
from {{ source('bronze', 'preauth_events') }}
