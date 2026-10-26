{# Small cross-database helpers so the same models build on DuckDB (local, CI) and Postgres (CI). #}

{% macro parse_yyyymmdd(column) %}
    {{ return(adapter.dispatch('parse_yyyymmdd')(column)) }}
{% endmacro %}

{% macro default__parse_yyyymmdd(column) %}
    to_date(nullif({{ column }}, ''), 'YYYYMMDD')
{% endmacro %}

{% macro duckdb__parse_yyyymmdd(column) %}
    cast(strptime(nullif({{ column }}, ''), '%Y%m%d') as date)
{% endmacro %}

{# Hours between two timestamps, with fractions. #}
{% macro hours_between(start, end) %}
    (extract(epoch from {{ end }}) - extract(epoch from {{ start }})) / 3600.0
{% endmacro %}

{# The masking policy: identifiers leave bronze only as salted MD5 hashes. #}
{% macro mask_id(column) %}
    md5('{{ var("pii_salt") }}' || {{ column }})
{% endmacro %}
