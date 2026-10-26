-- SCD Type 2 history from yearly snapshots. A new version starts only when a tracked attribute changes;
-- unchanged years are folded into the version before them. Coverage months are facts, not attributes.
{% set tracked = ['sex', 'race', 'state_code', 'county_code', 'has_esrd', 'death_date', 'has_alzheimers',
                  'has_heart_failure', 'has_kidney_disease', 'has_cancer', 'has_copd', 'has_depression',
                  'has_diabetes', 'has_ischemic_heart_disease', 'has_osteoporosis', 'has_arthritis', 'has_stroke_tia'] %}
with years as (
    select
        *,
        md5({% for c in tracked %}coalesce(cast({{ c }} as varchar), '~'){% if not loop.last %} || '|' || {% endif %}{% endfor %}) as attribute_hash
    from {{ ref('stg_synpuf__beneficiary_years') }}
),
changes as (
    select
        *,
        case when attribute_hash = lag(attribute_hash) over (partition by member_key order by file_year)
             then 0 else 1 end as is_new_version
    from years
),
versions as (
    select *, sum(is_new_version) over (partition by member_key order by file_year rows unbounded preceding) as version
    from changes
)
select
    member_key,
    version,
    min(file_year)                                                  as first_year,
    max(file_year)                                                  as last_year,
    {% for c in tracked %}any_value({{ c }}) as {{ c }},{% endfor %}
    any_value(birth_year)                                           as birth_year
from versions
group by member_key, version
