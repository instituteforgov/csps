# %%
"""
    Purpose
        Analyse the relationship between pay and benefits CSPS theme scores and pay data. Analyses two things:
            - Organisation-level EEI and theme scores for departments for 2024
            - CS median EEI and theme scores over time
    Inputs
        - XLSX: "Organisation working file.xlsx"
            - CSPS organisation data
        - XLSX: "Pay working file.xlsx"
            - Civil Service Stats pay data
    Outputs
        None
    Notes
        -- The coverage of the CSPS and Civil Service Stats are different. Differences are that:
            - Civil Service Stats include the security services
            - TODO: Expand
        -- See "analyse_theme_scores.py" for notes on the CSPS source data and analytical decisions made there: all points apply here too
        -- Figures ascribed to a department in our pay data are for core departments: we don't hold departmental group data in our version of the pay data
        -- There will be a slight mismatch in coverage for the DfE: CSPS data will be group figures while pay data will be core department only
"""

import os

import pandas as pd

import utils

# %%
# SET CONSTANTS
CSPS_PATH = "C:/Users/" + os.getlogin() + "/Institute for Government/Data - General/Civil service/Civil Service - People Survey/"
CSPS_FILE_NAME = "Organisation working file.xlsx"
CSPS_SHEET = "Data.Collated"
PAY_PATH = "C:/Users/" + os.getlogin() + "/Institute for Government/Data - General/Civil service/Civil Service - pay and high pay/"
PAY_FILE_NAME = "Pay working file.xlsx"
PAY_SHEET = "Collated.Organisation x grade"
PAY_NA_VALUES = ["[c]", "[n]"]

CSPS_MEDIAN_ORGANISATION_NAME = "Civil Service benchmark"
CSPS_MEAN_ORGANISATION_NAME = "All employees"
PAY_SUMMARY_ORGANISATION_NAME = "All employees"

CSPS_MIN_YEAR = 2010
CSPS_MAX_YEAR = 2024
CSPS_MEAN_MIN_YEAR = 2019

PAY_MIN_YEAR = 2010
PAY_MAX_YEAR = 2025

EEI_LABEL = "Employee Engagement Index"
TS_LABELS = [
    "Inclusion and fair treatment",
    "Leadership and managing change",
    "Learning and development",
    "My manager",
    "My team",
    "My work",
    "Organisational objectives and purpose",
    "Pay and benefits",
    "Resources and workload"
]

DEPT_GROUPS_TO_DROP = [
    "Scot Gov",
    "Welsh Gov"
]
ORGS_TO_DROP = [
    "Ministry of Justice group (including agencies)",
    "Office for National Statistics",
    "UK Statistics Authority (excluding Office for National Statistics)",
]

PAY_SUMMARY_GRADE_NAME = "All employees"

# NB: 'Organisations' that are dropped across all the organisation-level analysis - mean and median civil service figures - are intentionally not included here
DEPT_ONLY_CONDITIONS = {
    "organisation_type_filter": ["Ministerial department"],
    "exclude_orgs": ["Export Credits Guarantee Department"],
    "include_orgs": ["HM Revenue and Customs"],
}

# %%
# LOAD DATA
df_csps_organisation = pd.read_excel(CSPS_PATH + CSPS_FILE_NAME, sheet_name=CSPS_SHEET)
df_pay = pd.read_excel(PAY_PATH + PAY_FILE_NAME, sheet_name=PAY_SHEET, na_values=PAY_NA_VALUES)

# %%
# RUN CHECKS ON DATA
utils.check_csps_data(
    df_csps_organisation,
    CSPS_MIN_YEAR,
    CSPS_MAX_YEAR,
    CSPS_MEAN_MIN_YEAR,
    DEPT_GROUPS_TO_DROP,
    ORGS_TO_DROP,
    DEPT_ONLY_CONDITIONS,
    CSPS_MEDIAN_ORGANISATION_NAME,
    CSPS_MEAN_ORGANISATION_NAME,
    EEI_LABEL,
    TS_LABELS
)

utils.check_pay_data(
    df_pay,
    PAY_MIN_YEAR,
    PAY_MAX_YEAR,
    DEPT_GROUPS_TO_DROP,
    DEPT_ONLY_CONDITIONS,
    PAY_SUMMARY_ORGANISATION_NAME,
    PAY_SUMMARY_GRADE_NAME,
)

# %%
# EDIT DATA
df_csps_organisation_eei_ts = utils.edit_csps_data(
    df_csps_organisation,
    DEPT_GROUPS_TO_DROP,
    ORGS_TO_DROP
)

df_pay_cleaned = utils.edit_pay_data(
    df_pay,
    DEPT_GROUPS_TO_DROP,
)
