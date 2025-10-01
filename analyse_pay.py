# %%
"""
    Purpose
        Analyse the relationship between pay and benefits CSPS theme scores and pay data. Analyses two things:
            - Organisation-level EEI scores vs median pay, for 2024
            - Organisation-level pay and benefits theme scores vs median pay, for 2024
            - Core department organisation-level EEI scores vs median pay, for 2024
            - Core department organisation-level pay and benefits theme scores vs median pay, for 2024
            - CS median EEI scores vs median pay, over time
            - CS median pay and benefits theme scores vs median pay, over time
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
        -- CSPS is conducted in September-October each year, while pay date is as at the 31st March of the respective year
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
CSPS_DEPT_ONLY_CONDITIONS = {
    "organisation_type_filter": ["Ministerial department"],
    "exclude_orgs": ["Export Credits Guarantee Department"],
    "include_orgs": [
        "Department for Education group (including agencies)",
        "HM Revenue and Customs",
    ],
}
PAY_DEPT_ONLY_CONDITIONS = {
    "organisation_type_filter": ["Ministerial department"],
    "exclude_orgs": [
        "Export Credits Guarantee Department",
        "Office of the Secretary of State for Wales",
        "Northern Ireland Office",
        "Office of the Secretary of State for Scotland",
    ],
    "include_orgs": [
        "HM Revenue and Customs",
    ]
}

CSPS_ORGANISATION_RENAMINGS = {
    "Ministry of Housing, Communities & Local Government - 2024 iteration": "Ministry of Housing, Communities & Local Government",
    "Department for Education group (including agencies)": "Department for Education/Department for Education group",
}
PAY_ORGANISATION_RENAMINGS = {
    "Department for Levelling Up, Housing and Communities": "Ministry of Housing, Communities & Local Government",
    "Department for Education": "Department for Education/Department for Education group",
}

# %%
# CALCULATE VARIABLES
min_year = min(CSPS_MIN_YEAR, PAY_MIN_YEAR)
max_year = max(CSPS_MAX_YEAR, PAY_MAX_YEAR)

# %%
# LOAD DATA
df_csps = pd.read_excel(CSPS_PATH + CSPS_FILE_NAME, sheet_name=CSPS_SHEET)
df_pay = pd.read_excel(PAY_PATH + PAY_FILE_NAME, sheet_name=PAY_SHEET, na_values=PAY_NA_VALUES)

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

utils.check_pay_data(
    df_pay,
    PAY_MIN_YEAR,
    PAY_MAX_YEAR,
    DEPT_GROUPS_TO_DROP,
    PAY_DEPT_ONLY_CONDITIONS,
    PAY_SUMMARY_ORGANISATION_NAME,
    PAY_SUMMARY_GRADE_NAME,
)

# %%
# EDIT DATA
# Filter data
df_csps_eei_ts = utils.edit_csps_data(
    df_csps,
    DEPT_GROUPS_TO_DROP,
    ORGS_TO_DROP,
    min_year=min_year,
    max_year=max_year
)

df_pay_cleaned = utils.edit_pay_data(
    df_pay,
    DEPT_GROUPS_TO_DROP,
    min_year=min_year,
    max_year=max_year
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
# Create cuts of the pay data we'll need (organisation-level x 2024, department-level x 2024, CS median x all years)
df_pay_organisation2024 = df_pay_cleaned[
    (df_pay_cleaned["Year"] == 2024) &
    (df_pay_cleaned["Organisation"] != PAY_SUMMARY_ORGANISATION_NAME)
].copy()

df_pay_dept2024 = df_pay_cleaned[
    (df_pay_cleaned["Year"] == 2024) &
    (df_pay_cleaned["Organisation"] != PAY_SUMMARY_ORGANISATION_NAME) &
    (
        (df_pay_cleaned["Organisation type"].isin(PAY_DEPT_ONLY_CONDITIONS["organisation_type_filter"])) |
        (df_pay_cleaned["Organisation"].isin(PAY_DEPT_ONLY_CONDITIONS["include_orgs"]))
    ) &
    (~df_pay_cleaned["Organisation"].isin(PAY_DEPT_ONLY_CONDITIONS["exclude_orgs"]))
].copy()

df_pay_median = df_pay_cleaned[
    df_pay_cleaned["Organisation"] == PAY_SUMMARY_ORGANISATION_NAME
][["Year", "Median salary"]].copy()

# %%
# Rename organisations to facilitate merging
for df in [df_csps_eei_ts_organisation2024_pivot, df_csps_eei_ts_dept2024_pivot]:
    df["Organisation"] = df["Organisation"].replace(CSPS_ORGANISATION_RENAMINGS)
for df in [df_pay_organisation2024, df_pay_dept2024]:
    df["Organisation"] = df["Organisation"].replace(PAY_ORGANISATION_RENAMINGS)

# %%
# Check all organisations are matched between pay and CSPS data
csps_depts_2024 = set(df_csps_eei_ts_dept2024_pivot["Organisation"].unique())
pay_depts_2024 = set(df_pay_dept2024["Organisation"].unique())
csps_depts_2024_missing = csps_depts_2024 - pay_depts_2024
pay_depts_2024_missing = pay_depts_2024 - csps_depts_2024

assert len(csps_depts_2024_missing) == 0, f"CSPS department organisations missing from pay data: {csps_depts_2024_missing}"
assert len(pay_depts_2024_missing) == 0, f"Pay department organisations missing from CSPS data: {pay_depts_2024_missing}"

# %%
# Join CSPS and pay data, keeping only one set of organisation characteristics
df_pay_csps_organisation = df_pay_organisation2024[["Organisation", "Median salary"]].merge(
    df_csps_eei_ts_organisation2024_pivot,
    left_on="Organisation",
    right_on="Organisation",
    how="inner"
)
df_pay_csps_dept = df_pay_dept2024[["Organisation", "Median salary"]].merge(
    df_csps_eei_ts_dept2024_pivot,
    left_on="Organisation",
    right_on="Organisation",
    how="inner"
)
df_pay_csps_median = df_pay_median[["Year", "Median salary"]].merge(
    df_csps_eei_ts_median_pivot,
    on="Year",
    how="inner"
)

# %%
# ANALYSE DATA
# Organisation-level EEI scores vs median pay, for 2024
utils.draw_scatter_plot(
    df=df_pay_csps_organisation,
    x_var="Median salary",
    y_var=EEI_LABEL,
    height=3,
    hue="Organisation type",
    best_fit=True,
    fit_reg=False,
)

utils.fit_regressions(
    df_pay_csps_organisation, x_vars=["Median salary"], y_var=EEI_LABEL, data_description="2024 organisation-level data"
)

# %%
# Organisation-level pay and benefits theme scores vs median pay, for 2024
utils.draw_scatter_plot(
    df=df_pay_csps_organisation,
    x_var="Median salary",
    y_var="Pay and benefits",
    height=3,
    hue="Organisation type",
    best_fit=True,
    fit_reg=False,
)

utils.fit_regressions(
    df_pay_csps_organisation, x_vars=["Median salary"], y_var="Pay and benefits", data_description="2024 organisation-level data"
)

# %%
# Core department organisation-level EEI scores vs median pay, for 2024
utils.draw_scatter_plot(
    df=df_pay_csps_dept,
    x_var="Median salary",
    y_var=EEI_LABEL,
    height=3,
    hue="Organisation type",
    best_fit=True,
    fit_reg=False,
)

utils.fit_regressions(
    df_pay_csps_dept, x_vars=["Median salary"], y_var=EEI_LABEL, data_description="2024 organisation-level data, depts only"
)

# %%
# Core department organisation-level pay and benefits theme scores vs median pay, for 2024
utils.draw_scatter_plot(
    df=df_pay_csps_dept,
    x_var="Median salary",
    y_var="Pay and benefits",
    height=3,
    hue="Organisation type",
    best_fit=True,
    fit_reg=False,
)

utils.fit_regressions(
    df_pay_csps_dept, x_vars=["Median salary"], y_var="Pay and benefits", data_description="2024 organisation-level data, depts only"
)

# %%
# CS median EEI scores vs median pay, over time
utils.draw_scatter_plot(
    df=df_pay_csps_median,
    x_var="Median salary",
    y_var=EEI_LABEL,
    height=3,
    hue="Year",
    palette="rocket_r",
    best_fit=True,
    ci=None
)

utils.fit_regressions(
    df_pay_csps_median, x_vars=["Median salary"], y_var=EEI_LABEL, data_description="Civil service median EEI score vs median pay, over time"
)

# %%
# CS median pay and benefits theme scores vs median pay, over time
utils.draw_scatter_plot(
    df=df_pay_csps_median,
    x_var="Median salary",
    y_var="Pay and benefits",
    height=3,
    hue="Year",
    palette="rocket_r",
    best_fit=True,
    ci=None
)

utils.fit_regressions(
    df_pay_csps_median, x_vars=["Median salary"], y_var="Pay and benefits", data_description="Civil service median pay and benefits score vs median pay, over time"
)

# %%
