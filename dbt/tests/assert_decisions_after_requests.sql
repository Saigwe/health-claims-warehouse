-- A decision can't come before its request, and pending requests have no decision time.
select * from {{ ref('fct_preauth_request') }}
where decided_at < requested_at
   or (decision = 'pending' and decided_at is not null)
   or (decision <> 'pending' and decided_at is null)
