-- Point-in-time join: every claim line's member version was valid on its service date.
select f.claim_line_id
from {{ ref('fct_claim_line') }} f
join {{ ref('dim_member') }} m on m.member_sk = f.member_sk
where f.service_from_date not between m.valid_from and m.valid_to
