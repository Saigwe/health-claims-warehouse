-- Inpatient and outpatient claim segments in one shape. A segment-2 row carries no dates of its own, so it
-- takes them from segment 1 of the same claim.
with lines as (
    select 'inpatient' as setting, DESYNPUF_ID, CLM_ID, SEGMENT, CLM_FROM_DT, CLM_THRU_DT, PRVDR_NUM, CLM_PMT_AMT,
           NCH_PRMRY_PYR_CLM_PD_AMT, ICD9_DGNS_CD_1, CLM_ADMSN_DT, CLM_UTLZTN_DAY_CNT, CLM_DRG_CD,
           NCH_BENE_IP_DDCTBL_AMT as deductible, NCH_BENE_PTA_COINSRNC_LBLTY_AM as coinsurance
    from {{ source('bronze', 'inpatient_claims') }}
    union all
    select 'outpatient', DESYNPUF_ID, CLM_ID, SEGMENT, CLM_FROM_DT, CLM_THRU_DT, PRVDR_NUM, CLM_PMT_AMT,
           NCH_PRMRY_PYR_CLM_PD_AMT, ICD9_DGNS_CD_1, null, null, null,
           NCH_BENE_PTB_DDCTBL_AMT, NCH_BENE_PTB_COINSRNC_AMT
    from {{ source('bronze', 'outpatient_claims') }}
)
select
    setting || '-' || CLM_ID || '-' || SEGMENT                      as claim_line_id,
    setting,
    CLM_ID                                                          as claim_id,
    cast(SEGMENT as integer)                                        as segment,
    {{ mask_id('DESYNPUF_ID') }}                                    as member_key,
    PRVDR_NUM                                                       as provider_id,
    coalesce({{ parse_yyyymmdd('CLM_FROM_DT') }},
             max({{ parse_yyyymmdd('CLM_FROM_DT') }}) over (partition by setting, CLM_ID)) as service_from_date,
    coalesce({{ parse_yyyymmdd('CLM_THRU_DT') }},
             max({{ parse_yyyymmdd('CLM_THRU_DT') }}) over (partition by setting, CLM_ID)) as service_thru_date,
    {{ parse_yyyymmdd('CLM_ADMSN_DT') }}                             as admission_date,
    cast(CLM_PMT_AMT as numeric(14, 2))                             as paid_usd,
    cast(coalesce(NCH_PRMRY_PYR_CLM_PD_AMT, '0') as numeric(14, 2)) as other_payer_paid_usd,
    cast(coalesce(deductible, '0') as numeric(14, 2))               as deductible_usd,
    cast(coalesce(coinsurance, '0') as numeric(14, 2))              as coinsurance_usd,
    cast(CLM_UTLZTN_DAY_CNT as integer)                             as utilization_days,
    CLM_DRG_CD                                                      as drg_code,
    ICD9_DGNS_CD_1                                                  as primary_diagnosis_code
from lines
