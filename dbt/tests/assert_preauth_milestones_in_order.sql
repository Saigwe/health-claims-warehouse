-- Accumulating snapshot: milestones happen in order, and a decision exists exactly when the request is closed.
select request_id
from {{ ref('fct_preauth_request') }}
where info_requested_at < submitted_at
   or info_received_at < info_requested_at
   or decided_at < coalesce(info_received_at, submitted_at)
   or (decided_at is null) <> (status = 'open')
   or turnaround_hours < 0
