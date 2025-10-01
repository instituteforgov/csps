# %%
"""
    Purpose
        Analyse CSPS theme scores by organisation. Analyses three things:
            - Organisation-level EEI and theme scores for 2024
            - Core department organisation-level EEI and theme scores for 2024
            - CS median EEI and theme scores over time
    Inputs
        - XLSX: "Organisation working file.xlsx"
            - CSPS organisation data
    Outputs
        None
    Notes
        - Analysis is not carried out on CS mean figures, as there are insufficient data points: these are only available from 2019 onwards
        - Scottish and Welsh organisations are dropped, but this only applies to organisation-level analysis and not analysis based on the CS median
        - Four organisations are dropped to avoid double-counting:
            - 'Ministry of Justice group (including agencies)': Dropped as 'Ministry of Justice' (i.e. the core department) exists as a separate organisation in the data
            - 'Ministry of Justice arm's length bodies': Dropped as individual MoJ ALBs exist as separate organisations in the data
            - 'Office for National Statistics' and 'UK Statistics Authority (excluding Office for National Statistics)': Dropped as 'UK Statistics Authority', which includes the ONS, exists as a separate organisation in the data. ONS is a sub-unit rather than a distinct organisation, therefore we want to include it as part of UKSA
        - DfE figures included in this analysis are group figures, unlike other ministerial departments (see Excel working file for further details)
        - The department-only analysis is carried out on ministerial departments plus HMRC and minus Export Credits Guarantee Department, for consistency with other Whitehall Monitor analysis
        -- "Scotland, Wales and Northern Ireland Offices, and the Office of the Advocate General for Scotland" (with organisation type of "Combination" in our classification) is reported as one entity in CSPS and included in this analysis in that form
"""

import os

import pandas as pd

import utils

# %%
# SET CONSTANTS
CSPS_PATH = "C:/Users/" + os.getlogin() + "/Institute for Government/Data - General/Civil service/Civil Service - People Survey/"
CSPS_FILE_NAME = "Organisation working file.xlsx"
CSPS_SHEET = "Data.Collated"

CSPS_MEDIAN_ORGANISATION_NAME = "Civil Service benchmark"
CSPS_MEAN_ORGANISATION_NAME = "All employees"

CSPS_MIN_YEAR = 2010
CSPS_MAX_YEAR = 2024
CSPS_MEAN_MIN_YEAR = 2019

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
    "Ministry of Justice arm's length bodies",
    "Office for National Statistics",
    "UK Statistics Authority (excluding Office for National Statistics)",
]

# NB: 'Organisations' that are dropped across all the organisation-level analysis - mean and median civil service figures - are intentionally not included here
CSPS_DEPT_ONLY_CONDITIONS = {
    "organisation_type_filter": ["Ministerial department"],
    "exclude_orgs": ["Export Credits Guarantee Department"],
    "include_orgs": [
        "Department for Education group (including agencies)",
        "Scotland, Wales and Northern Ireland Offices, and the Office of the Advocate General for Scotland",
        "HM Revenue and Customs",
    ],
}

# %%
# LOAD DATA
df_csps = pd.read_excel(CSPS_PATH + CSPS_FILE_NAME, sheet_name=CSPS_SHEET)

# %%
# RUN CHECKS ON DATA
utils.check_csps_data(
    df_csps,
    CSPS_MIN_YEAR,
    CSPS_MAX_YEAR,
    CSPS_MEAN_MIN_YEAR,
    DEPT_GROUPS_TO_DROP,
    ORGS_TO_DROP,
    CSPS_DEPT_ONLY_CONDITIONS,
    CSPS_MEDIAN_ORGANISATION_NAME,
    CSPS_MEAN_ORGANISATION_NAME,
    EEI_LABEL,
    TS_LABELS
)

# %%
# EDIT DATA
# Filter data
df_csps_eei_ts = utils.edit_csps_data(
    df_csps,
    DEPT_GROUPS_TO_DROP,
    ORGS_TO_DROP
)

# %%
# Create cuts of the CSPS data we'll need (organisation-level x 2024, department-level x 2024, CS median x all years) and convert to wide format
df_csps_eei_ts_organisation2024_pivot = utils.filter_pivot_data(
    df_csps_eei_ts,
    year_filter=2024,
    exclude_orgs=[CSPS_MEDIAN_ORGANISATION_NAME, CSPS_MEAN_ORGANISATION_NAME],
    preserve_columns=["Organisation type"]
)

df_csps_eei_ts_dept2024_pivot = utils.filter_pivot_data(
    df_csps_eei_ts,
    year_filter=2024,
    organisation_type_filter=CSPS_DEPT_ONLY_CONDITIONS["organisation_type_filter"],
    exclude_orgs=[CSPS_MEDIAN_ORGANISATION_NAME, CSPS_MEAN_ORGANISATION_NAME] + CSPS_DEPT_ONLY_CONDITIONS["exclude_orgs"],
    include_orgs=CSPS_DEPT_ONLY_CONDITIONS["include_orgs"],
    preserve_columns=["Organisation type"]
)

df_csps_eei_ts_median_pivot = utils.filter_pivot_data(
    df_csps_eei_ts,
    organisation_filter=CSPS_MEDIAN_ORGANISATION_NAME,
)

# %%
# ANALYSE DATA
# Organisation-level EEI and theme scores for 2024
utils.draw_1d_pairplot(df_csps_eei_ts_organisation2024_pivot, x_vars=TS_LABELS, y_var=EEI_LABEL, hue="Organisation type")

utils.fit_regressions(
    df_csps_eei_ts_organisation2024_pivot, x_vars=TS_LABELS, y_var=EEI_LABEL, data_description="2024 organisation-level data"
)

# %%
# Organisation-level EEI and theme scores for departments for 2024
utils.draw_1d_pairplot(df_csps_eei_ts_dept2024_pivot, x_vars=TS_LABELS, y_var=EEI_LABEL, hue="Organisation type")

utils.fit_regressions(
    df_csps_eei_ts_dept2024_pivot, x_vars=TS_LABELS, y_var=EEI_LABEL, data_description="2024 organisation-level data, depts only"
)

# %%
# CS median EEI and theme scores over time
utils.draw_1d_pairplot(df_csps_eei_ts_median_pivot, x_vars=TS_LABELS, y_var=EEI_LABEL, hue="Year", palette="rocket_r")

utils.fit_regressions(
    df_csps_eei_ts_median_pivot, x_vars=TS_LABELS, y_var=EEI_LABEL, data_description="Civil service median data over time"
)

# %%
# Print significance legend and R² thresholds
print("Significance levels:")
print("*** p < 0.001")
print("**  p < 0.01")
print("*   p < 0.05")
print("    p ≥ 0.05 (not significant)")
print()

print("R² thresholds:")
print("R² = 0 = none")
print("0 < R² <= 0.1 = weak")
print("0.1 < R² <= 0.35 = moderate")
print("R² > 0.35 = strong")

# %%
