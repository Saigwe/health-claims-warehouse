-- SCD2 integrity: versions of a member never overlap, leave no gaps, and exactly one is current.
with v as (
    select member_key, version, valid_from, valid_to, is_current,
           lead(valid_from) over (partition by member_key order by version) as next_from
    from {{ ref('dim_member') }}
)
select member_key, 'overlap or gap' as problem from v where next_from is not null and next_from <> valid_to + 1
union all
select member_key, 'valid_to before valid_from' from v where valid_to < valid_from
union all
select member_key, 'not exactly one current version' from v group by member_key
having sum(case when is_current then 1 else 0 end) <> 1
