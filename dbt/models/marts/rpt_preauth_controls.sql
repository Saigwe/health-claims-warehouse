-- Control exceptions: inpatient admissions paid without an approved pre-authorisation, and why.
with admissions as (
    select claim_id, member_key, provider_id, coalesce(admission_date, service_from_date) as admission_date, paid_usd
    from {{ ref('fct_claim_line') }}
    where setting = 'inpatient' and segment = 1
),
classified as (
    select
        a.*,
        r.request_id,
        case when r.request_id is null then 'no request'
             when r.status = 'approved' then 'approved'
             else 'request ' || r.status end                       as authorisation
    from admissions a
    left join {{ ref('fct_preauth_request') }} r on r.matched_claim_id = a.claim_id
)
select
    authorisation,
    authorisation <> 'approved'                                     as is_exception,
    count(*)                                                        as admissions,
    sum(paid_usd)                                                   as paid_usd
from classified
group by 1, 2
