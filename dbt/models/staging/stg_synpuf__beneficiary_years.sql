-- One row per member per year. Masking policy: the raw beneficiary id and full birth date stop here;
-- downstream sees a salted hash and the birth year only.
select
    {{ mask_id('DESYNPUF_ID') }}                                    as member_key,
    cast(file_year as integer)                                      as file_year,
    cast(substr(BENE_BIRTH_DT, 1, 4) as integer)                    as birth_year,
    {{ parse_yyyymmdd('BENE_DEATH_DT') }}                            as death_date,
    case BENE_SEX_IDENT_CD when '1' then 'Male' when '2' then 'Female' end as sex,
    case BENE_RACE_CD when '1' then 'White' when '2' then 'Black' when '3' then 'Other'
                      when '5' then 'Hispanic' end                  as race,
    SP_STATE_CODE                                                   as state_code,
    BENE_COUNTY_CD                                                  as county_code,
    BENE_ESRD_IND = 'Y'                                             as has_esrd,
    cast(BENE_HI_CVRAGE_TOT_MONS as integer)                        as part_a_months,
    cast(BENE_SMI_CVRAGE_TOT_MONS as integer)                       as part_b_months,
    cast(BENE_HMO_CVRAGE_TOT_MONS as integer)                       as hmo_months,
    SP_ALZHDMTA = '1' as has_alzheimers, SP_CHF = '1' as has_heart_failure, SP_CHRNKIDN = '1' as has_kidney_disease,
    SP_CNCR = '1' as has_cancer, SP_COPD = '1' as has_copd, SP_DEPRESSN = '1' as has_depression,
    SP_DIABETES = '1' as has_diabetes, SP_ISCHMCHT = '1' as has_ischemic_heart_disease,
    SP_OSTEOPRS = '1' as has_osteoporosis, SP_RA_OA = '1' as has_arthritis, SP_STRKETIA = '1' as has_stroke_tia,
    cast(MEDREIMB_IP as numeric(14, 2))                             as summary_inpatient_paid_usd,
    cast(MEDREIMB_OP as numeric(14, 2))                             as summary_outpatient_paid_usd
from {{ source('bronze', 'beneficiary_summary') }}
