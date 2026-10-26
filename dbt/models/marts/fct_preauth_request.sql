-- Accumulating snapshot: one row per pre-authorisation request, with a timestamp column per milestone that
-- fills in as the request moves on. Turnaround stops the clock while the payer waits for information
-- (the industry "pend" rule). The request is matched to the claim the way a payer does: same member and
-- provider, admitted within var('match_window_days') of the planned date; each claim matches one request.
{% set window = var('match_window_days') %}
with ev as (select * from {{ ref('stg_preauth__events') }}),
req as (
    select
        request_id,
        max(member_key)                                             as member_key,
        max(provider_id)                                            as provider_id,
        max(priority)                                               as priority,
        max(drg_code)                                               as drg_code,
        max(planned_admission_date)                                 as planned_admission_date,
        max(case when event_type = 'submitted' then event_at end)   as submitted_at,
        max(case when event_type = 'info_requested' then event_at end) as info_requested_at,
        max(case when event_type = 'info_received' then event_at end) as info_received_at,
        max(case when event_type in ('approved', 'denied', 'withdrawn') then event_at end) as decided_at,
        coalesce(max(case when event_type in ('approved', 'denied', 'withdrawn') then event_type end), 'open') as status
    from ev
    group by 1
),
admissions as (
    select claim_id, member_key, provider_id, coalesce(admission_date, service_from_date) as admission_date, paid_usd
    from {{ ref('fct_claim_line') }}
    where setting = 'inpatient' and segment = 1
),
candidates as (
    select
        r.request_id, a.claim_id, a.paid_usd, a.admission_date,
        row_number() over (partition by r.request_id
                           order by abs(a.admission_date - r.planned_admission_date), a.claim_id) as rank_for_request,
        row_number() over (partition by a.claim_id
                           order by abs(a.admission_date - r.planned_admission_date), r.request_id) as rank_for_claim
    from req r
    join admissions a
      on a.member_key = r.member_key and a.provider_id = r.provider_id
     and a.admission_date between r.planned_admission_date - {{ window }} and r.planned_admission_date + {{ window }}
),
matched as (select * from candidates where rank_for_request = 1 and rank_for_claim = 1),
timed as (
    select
        r.*,
        {{ hours_between('r.submitted_at', 'r.decided_at') }}       as elapsed_hours,
        coalesce({{ hours_between('r.info_requested_at', 'r.info_received_at') }}, 0) as pended_hours
    from req r
)
select
    t.request_id,
    m.member_sk,
    t.member_key,
    t.provider_id,
    t.priority,
    t.drg_code,
    t.planned_admission_date,
    t.submitted_at,
    t.info_requested_at,
    t.info_received_at,
    t.decided_at,
    t.status,
    t.info_requested_at is not null                                 as was_pended,
    t.elapsed_hours,
    t.elapsed_hours - t.pended_hours                                as turnaround_hours,
    case when t.decided_at is null then null
         else t.elapsed_hours - t.pended_hours <= case when t.priority = 'urgent' then {{ var('sla_hours_urgent') }}
                                                       else {{ var('sla_hours_standard') }} end
    end                                                             as met_sla,
    x.claim_id                                                      as matched_claim_id,
    x.admission_date                                                as matched_admission_date,
    x.paid_usd                                                      as matched_claim_paid_usd
from timed t
left join matched x on x.request_id = t.request_id
left join {{ ref('dim_member') }} m
    on m.member_key = t.member_key and cast(t.submitted_at as date) between m.valid_from and m.valid_to
