-- Every claim segment and every cent loaded reaches the fact or the quarantine table, per setting.
with b as (
    select 'inpatient' as setting, count(*) as n, sum(cast(CLM_PMT_AMT as numeric(14, 2))) as paid
    from {{ source('bronze', 'inpatient_claims') }}
    union all
    select 'outpatient', count(*), sum(cast(CLM_PMT_AMT as numeric(14, 2))) from {{ source('bronze', 'outpatient_claims') }}
),
f as (
    select setting, count(*) as n, sum(paid_usd) as paid from (
        select setting, paid_usd from {{ ref('fct_claim_line') }}
        union all
        select setting, paid_usd from {{ ref('qa_claim_lines_without_dates') }}
    ) x group by 1
)
select b.setting from b left join f on f.setting = b.setting
where f.n is null or f.n <> b.n or abs(f.paid - b.paid) > 0.01
