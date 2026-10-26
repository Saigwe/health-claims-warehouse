-- Masking policy, enforced: nothing outside bronze may carry a raw identifier or a full birth date.
--  1. no silver/gold column is named like a raw identifier or birth date
--  2. every member_key is a 32-character hash, and none equals a raw beneficiary id
select table_schema || '.' || table_name || '.' || column_name as problem
from information_schema.columns
where table_schema in ('silver', 'gold')
  and (lower(column_name) like '%desynpuf%' or lower(column_name) like '%birth_dt%'
       or lower(column_name) in ('member_id', 'date_of_birth', 'birth_date', 'npi', 'at_physn_npi'))
union all
select 'member_key not a hash: ' || member_key from {{ ref('dim_member') }} where length(member_key) <> 32
union all
select 'raw id leaked into dim_member' from {{ ref('dim_member') }} m
where m.member_key in (select DESYNPUF_ID from {{ source('bronze', 'beneficiary_summary') }})
union all
select 'raw id leaked into fct_preauth_request' from {{ ref('fct_preauth_request') }} r
where r.member_key in (select member_id from {{ source('bronze', 'preauth_events') }})
