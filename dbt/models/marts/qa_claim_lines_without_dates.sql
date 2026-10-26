-- Quarantine: claim segments with no service date anywhere on the claim (a segment 2 whose segment 1 is
-- missing from the CMS file). Kept, counted and reconciled, but not reported as cost in any period.
select claim_line_id, setting, claim_id, segment, member_key, provider_id, paid_usd
from {{ ref('stg_synpuf__claim_lines') }}
where service_from_date is null
