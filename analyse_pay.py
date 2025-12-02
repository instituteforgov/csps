# %%
"""
    Purpose
        Analyse the relationship between CSPS results (overall engagement, pay and benefits theme scores) and pay data. Carries out the following:
            - Simple linear regressions
                - Organisation-level EEI scores vs median HEO/SEO pay, for 2024 (morale data) and 2025 (pay data)
                - Organisation-level pay and benefits theme scores vs median HEO/SEO pay, for 2024 (morale data) and 2025 (pay data)
                - Core department organisation-level EEI scores vs median HEO/SEO pay, for 2024 (morale data) and 2025 (pay data)
                - Core department organisation-level pay and benefits theme scores vs median HEO/SEO pay, for 2024 (morale data) and 2025 (pay data)
                - CS median EEI scores vs median HEO/SEO pay, over time
                - CS median pay and benefits theme scores vs median HEO/SEO pay, over time
            - Two-way fixed effects regressions
                - Organisation-level EEI scores vs median HEO/SEO pay (all years)
                - Organisation-level pay and benefits theme scores vs median HEO/SEO pay (all years)
                - Core department organisation-level EEI scores vs median HEO/SEO pay (all years)
                - Core department organisation-level pay and benefits theme scores vs median HEO/SEO pay (all years)
    Inputs
        - XLSX: "Organisation working file.xlsx"
            - CSPS organisation data
        - XLSX: "Pay working file.xlsx"
            - Civil Service Stats pay data
        - API: https://api.beta.ons.gov.uk/v1/data?uri=/economy/inflationandpriceindices/timeseries/d7bt/mm23
            - ONS CPI Index 00 data (https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23)
    Outputs
        None
    Notes
        - See "analyse_theme_scores.py" for notes on the CSPS source data, analytical decisions made there and caveats on the two-way fixed effects analysis: all points apply here too unless otherwise stated
        - This focuses on HEO/SEO pay to try and remove the effect of different grade distributions between organisations. HEO/SEO is chosen as it is the biggest band overall across the civil service and the biggest band in departments of interest
        - Pay is put into real terms using CPI as the deflator. The April CPI rate is used, for consistency with convention in WM, agreed with Tom
        - CSPS is conducted in September-October each year, while pay date is as at the 31st March of the respective year. CSPS data for a given year is matched to pay data for the following year (i.e. 2024 CSPS data is matched to 2025 pay data). This is on the thinking that pay awards happen between the start of the financial year and the time of the CSPS survey, therefore pay awards made in 2024/25 will first show up in the 2024 CSPS data and 2025 pay data
        - Median HEO/SEO pay is available for a smaller group of organisations than overall median pay - due to e.g. suppression of small numbers - therefore the analysis is based on a smaller list of organisations than the totality of the pay dataset. Organisations for which median HEO/SEO pay is not available are printed alongside the outputs of the analysis
        - The coverage of the CSPS and Civil Service Stats are different. Differences are that:
            - Civil Service Stats include the following as an organisation, while CSPS does not:
                - 'Security and Intelligence Services': Other public body
                - 'Central Civil Service Fast Stream': Ministerial dept sub-unit
                - 'Defence Electronics and Components Agency': Exec agency sub-unit (since 2023)
                - 'Government Commercial Organisation': Ministerial dept sub-unit
                - 'Office for Budget Responsibility' : Exec NDPB - unclear why not in CSPS
                - 'Queen Elizabeth II Centre': Exec agency - unclear why not in CSPS
                - 'Royal Fleet Auxiliary': Exec agency - unclear why not in CSPS
                - 'UK Supreme Court' : NMD - unclear why not in CSPS
            - CSPS includes 'HM Inspectorate of Constabulary and Fire and Rescue Services' (an 'Other public body', per CO's classification), while Civil Service Stats do not
            - "Scotland, Wales and Northern Ireland Offices, and the Office of the Advocate General for Scotland" is included as one entity in the CSPS data, while the territorial offices are separate entities in the pay data
        - Figures ascribed to a department in our pay data are for core departments: we don't hold departmental group data in our version of the pay data
        - In the organisation-level analysis, coverage differs slightly between this analysis and the CSPS theme score analysis:
            - "HM Inspectorate of Constabulary and Fire and Rescue Services" (CSPS data) is dropped from this analysis as it doesn't exist in the pay data,
            - "Scotland, Wales and Northern Ireland Offices, and the Office of the Advocate General for Scotland" (CSPS data) and "Office of the Secretary of State for Scotland"/"Office of the Secretary of State for Wales"/"Northern Ireland Office" (pay data) are dropped from this analysis as they can't easily be matched
            - "HM Prison and Probation Service (excluding HM Prison Service and National Probation Service/Probation Service)"/"HM Prison Service"/"Probation Service" (CSPS data) and "HM Prison and Probation Service" are dropped from this analysis as they can't easily be matched
        - There is also a slight mismatch in coverage for DfE: CSPS data is group figures while pay data is the core department only (departmental group bodies have been excluded from the pay data)
    Future enhancements
        - See "analyse_theme_scores.py"
        - Turn years-of-interest into constants
"""

import os

from IPython.display import display
import pandas as pd
import requests
import seaborn as sns

import utils

# %%
# SET CONSTANTS
CSPS_PATH_OPTIONS = [
    "C:/Users/" + os.getlogin() + "/Institute for Government/Data - General/Civil service/Civil Service - People Survey/",
    "C:/Users/" + os.getlogin() + "/OneDrive - Institute for Government/Data - Civil service/Civil Service - People Survey/"
]
CSPS_FILE_NAME = "Organisation working file.xlsx"
CSPS_SHEET = "Data.Collated"
PAY_PATH_OPTIONS = [
    "C:/Users/" + os.getlogin() + "/Institute for Government/Data - General/Civil service/Civil Service - pay and high pay/",
    "C:/Users/" + os.getlogin() + "/OneDrive - Institute for Government/Data - Civil service/Civil Service - pay and high pay/"
]
PAY_FILE_NAME = "Pay working file.xlsx"
PAY_SHEET = "Collated.Organisation x grade"
PAY_NA_VALUES = ["[c]", "[n]", "-", ".."]
CPI_API_URL = "https://api.beta.ons.gov.uk/v1/data?uri=/economy/inflationandpriceindices/timeseries/d7bt/mm23"
CPI_DEFLATOR_MIN_YEAR = 2010
CPI_DEFLATOR_MAX_YEAR = 2025
CPI_DEFLATOR_MONTH = "April"
CPI_DEFLATOR_BASE_YEAR = 2025

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

CSPS_ORGS_TO_DROP = [
    "Ministry of Justice group (including agencies)",
    "Ministry of Justice arm's length bodies",
    "Office for National Statistics",
    "UK Statistics Authority (excluding Office for National Statistics)",
]

PAY_TARGET_GRADE_NAME = "SEO/HEO"

PAY_MEASURE_COLUMN = "Median salary"

# NB: 'Organisations' that are dropped across all the organisation-level analysis - mean and median civil service figures - are intentionally not included here
CSPS_ORGANISATION_ONLY_CONDITIONS = {
    "exclude_orgs": [
        "Scotland, Wales and Northern Ireland Offices, and the Office of the Advocate General for Scotland",
        "HM Prison and Probation Service (excluding HM Prison Service and National Probation Service/Probation Service)",
        "HM Prison Service",
        "Probation Service",
        "HM Inspectorate of Constabulary and Fire and Rescue Services",
    ],
}
PAY_ORGANISATION_ONLY_CONDITIONS = {
    "exclude_orgs": [
        "Office of the Secretary of State for Scotland",
        "Office of the Secretary of State for Wales",
        "Northern Ireland Office",
        "HM Prison and Probation Service",
        "Security and Intelligence Services",
        "Central Civil Service Fast Stream",
        "Defence Electronics and Components Agency",
        "Government Commercial Organisation",
        "Office for Budget Responsibility",
        "Queen Elizabeth II Centre",
        "Royal Fleet Auxiliary",
        "UK Supreme Court",
        "Education and Skills Funding Agency",
        "Standards and Testing Agency",
        "Teaching Regulation Agency",
    ],
}
CSPS_DEPT_ONLY_CONDITIONS = {
    "organisation_type_filter": ["Ministerial department"],
    "exclude_orgs": [
        "Attorney General's Office",
        "Export Credits Guarantee Department"
    ],
    "include_orgs": [
        "Department for Education group (including agencies)",
        "HM Revenue and Customs",
    ],
}
PAY_DEPT_ONLY_CONDITIONS = {
    "organisation_type_filter": ["Ministerial department"],
    "exclude_orgs": [
        "Attorney General's Office",
        "Export Credits Guarantee Department",
        "Office of the Secretary of State for Scotland",
        "Office of the Secretary of State for Wales",
        "Northern Ireland Office",
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
    "Ministry of Housing, Communities & Local Government - 2024 iteration": "Ministry of Housing, Communities & Local Government",
    "Department for Education": "Department for Education/Department for Education group",
    "Medicines and Healthcare Products Regulatory Agency": "Medicines and Healthcare products Regulatory Agency",
}

# %%
# LOAD DATA
# Try to load from each path option until one works
for path in CSPS_PATH_OPTIONS:
    try:
        df_csps = pd.read_excel(path + CSPS_FILE_NAME, sheet_name=CSPS_SHEET)
        print(f"Loaded data from {path}")
        break
    except FileNotFoundError:
        print(f"File not found in {path}, trying next option...")

for path in PAY_PATH_OPTIONS:
    try:
        df_pay = pd.read_excel(path + PAY_FILE_NAME, sheet_name=PAY_SHEET, na_values=PAY_NA_VALUES)
        print(f"Loaded pay data from {path}")
        break
    except FileNotFoundError:
        print(f"File not found in {path}, trying next option...")

# Load CPI data from ONS API
print("Fetching CPI data from ONS API...")
response = requests.get(CPI_API_URL)
response.raise_for_status()
cpi_data = response.json()

# Extract monthly observations from API response
months = cpi_data.get('months', [])

# Convert to DataFrame
df_cpi = pd.DataFrame(months)

# Filter for April records between the min and max years
df_cpi = df_cpi[
    (df_cpi['month'] == CPI_DEFLATOR_MONTH) &
    (df_cpi['year'].astype(int) >= CPI_DEFLATOR_MIN_YEAR) &
    (df_cpi['year'].astype(int) <= CPI_DEFLATOR_MAX_YEAR)
].copy()

# Extract year and CPI value
df_cpi['Year'] = df_cpi['year'].astype(int)
df_cpi['CPI'] = df_cpi['value'].astype(float)
df_cpi = df_cpi[['Year', 'CPI']]

print(f"Loaded CPI data from ONS API ({len(df_cpi)} records)")

# %%
# RUN CHECKS ON DATA
utils.check_csps_data(
    df_csps,
    CSPS_MIN_YEAR,
    CSPS_MAX_YEAR,
    CSPS_MEAN_MIN_YEAR,
    DEPT_GROUPS_TO_DROP,
    CSPS_ORGS_TO_DROP,
    CSPS_DEPT_ONLY_CONDITIONS,
    CSPS_MEDIAN_ORGANISATION_NAME,
    CSPS_MEAN_ORGANISATION_NAME,
    EEI_LABEL,
    TS_LABELS
)

utils.check_csstats_data(
    df_pay,
    PAY_MIN_YEAR,
    PAY_MAX_YEAR,
    DEPT_GROUPS_TO_DROP,
    PAY_DEPT_ONLY_CONDITIONS,
    PAY_SUMMARY_ORGANISATION_NAME,
    PAY_TARGET_GRADE_NAME,
)

# %%
# EDIT DATA
# Filter data
df_csps_eei_ts = utils.edit_csps_data(
    df=df_csps,
    dept_groups_to_drop=DEPT_GROUPS_TO_DROP,
    orgs_to_drop=CSPS_ORGS_TO_DROP,
    min_year=CSPS_MIN_YEAR,
    max_year=CSPS_MAX_YEAR
)

df_pay_cleaned = utils.edit_csstats_data(
    df=df_pay,
    target_grade_name=PAY_TARGET_GRADE_NAME,
    dept_groups_to_drop=DEPT_GROUPS_TO_DROP,
    measure_column=PAY_MEASURE_COLUMN,
    min_year=PAY_MIN_YEAR,
    max_year=PAY_MAX_YEAR
)

# %%
# Create cuts of the CSPS data we'll need (CS median x all years, organisation-level x 2024, department-level x 2024, organisation-level x all years, department-level x all years) and convert to wide format
df_csps_eei_ts_median_pivot = utils.filter_pivot_data(
    df_csps_eei_ts,
    organisation_filter=CSPS_MEDIAN_ORGANISATION_NAME,
)

df_csps_eei_ts_organisation2024_pivot = utils.filter_pivot_data(
    df_csps_eei_ts,
    year_filter=2024,
    exclude_orgs=[CSPS_MEDIAN_ORGANISATION_NAME, CSPS_MEAN_ORGANISATION_NAME] + CSPS_ORGANISATION_ONLY_CONDITIONS["exclude_orgs"],
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

df_csps_eei_ts_organisation_pivot = utils.filter_pivot_data(
    df_csps_eei_ts,
    exclude_orgs=[CSPS_MEDIAN_ORGANISATION_NAME, CSPS_MEAN_ORGANISATION_NAME] + CSPS_ORGANISATION_ONLY_CONDITIONS["exclude_orgs"],
    preserve_columns=["Organisation type"]
)

df_csps_eei_ts_dept_pivot = utils.filter_pivot_data(
    df_csps_eei_ts,
    organisation_type_filter=CSPS_DEPT_ONLY_CONDITIONS["organisation_type_filter"],
    exclude_orgs=[CSPS_MEDIAN_ORGANISATION_NAME, CSPS_MEAN_ORGANISATION_NAME] + CSPS_DEPT_ONLY_CONDITIONS["exclude_orgs"],
    include_orgs=CSPS_DEPT_ONLY_CONDITIONS["include_orgs"],
    preserve_columns=["Organisation type"]
)

# %%
# Create cuts of the pay data we'll need (CS median x all years, organisation-level x 2025, department-level x 2025, organisation-level x all years, department-level x all years)
df_pay_median = df_pay_cleaned[
    df_pay_cleaned["Organisation"] == PAY_SUMMARY_ORGANISATION_NAME
][["Year", "Median salary"]].copy()

df_pay_organisation2025 = df_pay_cleaned[
    (df_pay_cleaned["Year"] == 2025) &
    (df_pay_cleaned["Organisation"] != PAY_SUMMARY_ORGANISATION_NAME) &
    (~df_pay_cleaned["Organisation"].isin(PAY_ORGANISATION_ONLY_CONDITIONS["exclude_orgs"]))
].copy()

df_pay_dept2025 = df_pay_cleaned[
    (df_pay_cleaned["Year"] == 2025) &
    (df_pay_cleaned["Organisation"] != PAY_SUMMARY_ORGANISATION_NAME) &
    (
        (df_pay_cleaned["Organisation type"].isin(PAY_DEPT_ONLY_CONDITIONS["organisation_type_filter"])) |
        (df_pay_cleaned["Organisation"].isin(PAY_DEPT_ONLY_CONDITIONS["include_orgs"]))
    ) &
    (~df_pay_cleaned["Organisation"].isin(PAY_DEPT_ONLY_CONDITIONS["exclude_orgs"]))
].copy()

df_pay_organisation = df_pay_cleaned[
    (df_pay_cleaned["Organisation"] != PAY_SUMMARY_ORGANISATION_NAME) &
    (~df_pay_cleaned["Organisation"].isin(PAY_ORGANISATION_ONLY_CONDITIONS["exclude_orgs"]))
].copy()

df_pay_dept = df_pay_cleaned[
    (df_pay_cleaned["Organisation"] != PAY_SUMMARY_ORGANISATION_NAME) &
    (
        (df_pay_cleaned["Organisation type"].isin(PAY_DEPT_ONLY_CONDITIONS["organisation_type_filter"])) |
        (df_pay_cleaned["Organisation"].isin(PAY_DEPT_ONLY_CONDITIONS["include_orgs"]))
    ) &
    (~df_pay_cleaned["Organisation"].isin(PAY_DEPT_ONLY_CONDITIONS["exclude_orgs"]))
].copy()

# %%
# Rename organisations to facilitate merging
for df in [df_csps_eei_ts_organisation2024_pivot, df_csps_eei_ts_dept2024_pivot, df_csps_eei_ts_organisation_pivot, df_csps_eei_ts_dept_pivot]:
    df["Organisation"] = df["Organisation"].replace(CSPS_ORGANISATION_RENAMINGS)
for df in [df_pay_organisation2025, df_pay_dept2025, df_pay_organisation, df_pay_dept]:
    df["Organisation"] = df["Organisation"].replace(PAY_ORGANISATION_RENAMINGS)

# %%
# Check all organisations are matched between pay and CSPS data
csps_organisations_2024 = set(df_csps_eei_ts_organisation2024_pivot["Organisation"].unique())
pay_organisations_2025 = set(df_pay_organisation2025["Organisation"].unique())
csps_organisations_2024_missing = csps_organisations_2024 - pay_organisations_2025
pay_organisations_2025_missing = pay_organisations_2025 - csps_organisations_2024

assert len(csps_organisations_2024_missing) == 0, f"CSPS organisations missing from pay data: {csps_organisations_2024_missing}"
assert len(pay_organisations_2025_missing) == 0, f"Pay organisations missing from CSPS data: {pay_organisations_2025_missing}"

# %%
csps_depts_2024 = set(df_csps_eei_ts_dept2024_pivot["Organisation"].unique())
pay_depts_2025 = set(df_pay_dept2025["Organisation"].unique())
csps_depts_2024_missing = csps_depts_2024 - pay_depts_2025
pay_depts_2025_missing = pay_depts_2025 - csps_depts_2024

assert len(csps_depts_2024_missing) == 0, f"CSPS departments missing from pay data: {csps_depts_2024_missing}"
assert len(pay_depts_2025_missing) == 0, f"Pay departments missing from CSPS data: {pay_depts_2025_missing}"

# %%
# Join CSPS and pay data, keeping only one set of organisation characteristics in organisation-level analysis
# Adjust CSPS years to match pay years (CSPS year Y matches Pay year Y+1)
df_pay_csps_median = df_pay_median[["Year", "Median salary"]].merge(
    df_csps_eei_ts_median_pivot.assign(Year=df_csps_eei_ts_median_pivot["Year"] + 1),
    on="Year",
    how="inner"
)
df_pay_csps_organisation = df_pay_organisation2025[["Organisation", "Median salary"]].merge(
    df_csps_eei_ts_organisation2024_pivot,
    left_on="Organisation",
    right_on="Organisation",
    how="inner"
)
df_pay_csps_dept = df_pay_dept2025[["Organisation", "Median salary"]].merge(
    df_csps_eei_ts_dept2024_pivot,
    left_on="Organisation",
    right_on="Organisation",
    how="inner"
)
df_pay_csps_organisation_panel = df_pay_organisation[["Organisation", "Year", "Median salary"]].merge(
    df_csps_eei_ts_organisation_pivot.assign(Year=df_csps_eei_ts_organisation_pivot["Year"] + 1),
    on=["Organisation", "Year"],
    how="inner"
)
df_pay_csps_dept_panel = df_pay_dept[["Organisation", "Year", "Median salary"]].merge(
    df_csps_eei_ts_dept_pivot.assign(Year=df_csps_eei_ts_dept_pivot["Year"] + 1),
    on=["Organisation", "Year"],
    how="inner"
)

# %%
# Deflate pay data
# NB: For single-year dataframes, this only involves multiplying 'Median salary' by the relevant deflator
cpi_base_year = df_cpi[df_cpi["Year"] == CPI_DEFLATOR_BASE_YEAR]["CPI"].values[0]
df_cpi["Deflator"] = cpi_base_year / df_cpi["CPI"]
df_cpi_deflators = df_cpi[["Year", "Deflator"]]
df_pay_csps_median = df_pay_csps_median.merge(
    df_cpi_deflators,
    on="Year",
    how="left"
)
df_pay_csps_median["Median salary deflated"] = df_pay_csps_median["Median salary"] * df_pay_csps_median["Deflator"]
df_pay_csps_median.drop(columns=["Deflator"], inplace=True)

df_pay_csps_organisation["Median salary deflated"] = df_pay_csps_organisation["Median salary"] * df_cpi_deflators[
    df_cpi_deflators["Year"] == CPI_DEFLATOR_BASE_YEAR
]["Deflator"].values[0]

df_pay_csps_organisation_panel = df_pay_csps_organisation_panel.merge(
    df_cpi_deflators,
    on="Year",
    how="left"
)
df_pay_csps_organisation_panel["Median salary deflated"] = df_pay_csps_organisation_panel["Median salary"] * df_pay_csps_organisation_panel["Deflator"]
df_pay_csps_organisation_panel.drop(columns=["Deflator"], inplace=True)

df_pay_csps_dept["Median salary deflated"] = df_pay_csps_dept["Median salary"] * df_cpi_deflators[
    df_cpi_deflators["Year"] == CPI_DEFLATOR_BASE_YEAR
]["Deflator"].values[0]

df_pay_csps_dept_panel = df_pay_csps_dept_panel.merge(
    df_cpi_deflators,
    on="Year",
    how="left"
)
df_pay_csps_dept_panel["Median salary deflated"] = df_pay_csps_dept_panel["Median salary"] * df_pay_csps_dept_panel["Deflator"]
df_pay_csps_dept_panel.drop(columns=["Deflator"], inplace=True)

# %%
# Plot 'Median salary deflated' over time
sns.set_theme(style="whitegrid")
plt = sns.lineplot(
    data=df_pay_csps_median,
    x="Year",
    y="Median salary deflated",
    marker="o"
)

# %%
# ANALYSE DATA
# CS median EEI scores vs median HEO/SEO pay regression, over time
utils.draw_scatter_plot(
    df=df_pay_csps_median,
    x_var="Median salary deflated",
    y_var=EEI_LABEL,
    height=3,
    hue="Year",
    palette="rocket_r",
    best_fit=True,
    ci=None
)

utils.fit_regressions(
    df_pay_csps_median, x_vars=["Median salary deflated"], y_var=EEI_LABEL, data_description="Civil service median EEI score vs median HEO/SEO pay, over time"
)

# %%
# CS median pay and benefits theme scores vs median HEO/SEO pay regression, over time
utils.draw_scatter_plot(
    df=df_pay_csps_median,
    x_var="Median salary deflated",
    y_var="Pay and benefits",
    height=3,
    hue="Year",
    palette="rocket_r",
    best_fit=True,
    ci=None
)

utils.fit_regressions(
    df_pay_csps_median, x_vars=["Median salary deflated"], y_var="Pay and benefits", data_description="Civil service median pay and benefits score vs median HEO/SEO pay, over time"
)

# %%
# CS median HEO/SEO pay records with missing median salary
display(
    df_pay_csps_median[
        df_pay_csps_median["Median salary deflated"].isna()
    ]
)

# %%
# Organisation-level EEI scores vs median HEO/SEO pay regression, for 2024 (morale data) and 2025 (pay data)
utils.draw_scatter_plot(
    df=df_pay_csps_organisation,
    x_var="Median salary deflated",
    y_var=EEI_LABEL,
    height=3,
    hue="Organisation type",
    best_fit=True,
    fit_reg=False,
)

utils.fit_regressions(
    df_pay_csps_organisation, x_vars=["Median salary deflated"], y_var=EEI_LABEL, data_description="2024 organisation-level data"
)

# %%
# Organisation-level EEI scores vs median HEO/SEO pay two-way fixed effects regression
utils.fit_fixed_effects_regression(
    df_pay_csps_organisation_panel,
    x_var="Median salary deflated",
    y_var=EEI_LABEL,
    entity_var="Organisation",
    time_var="Year",
    data_description="Organisation-level panel data"
)

# %%
# Organisation-level pay and benefits theme scores vs median HEO/SEO pay regression, for 2024 (morale data) and 2025 (pay data)
utils.draw_scatter_plot(
    df=df_pay_csps_organisation,
    x_var="Median salary deflated",
    y_var="Pay and benefits",
    height=3,
    hue="Organisation type",
    best_fit=True,
    fit_reg=False,
)

utils.fit_regressions(
    df_pay_csps_organisation, x_vars=["Median salary deflated"], y_var="Pay and benefits", data_description="2024 organisation-level data"
)

# %%
# Organisation-level pay and benefits theme scores vs median HEO/SEO pay two-way fixed effects regression
utils.fit_fixed_effects_regression(
    df_pay_csps_organisation_panel,
    x_var="Median salary deflated",
    y_var="Pay and benefits",
    entity_var="Organisation",
    time_var="Year",
    data_description="Organisation-level panel data"
)

# %%
# Organisation-level HEO/SEO pay records with missing median salary
display(
    df_pay_csps_organisation[
        df_pay_csps_organisation["Median salary deflated"].isna()
    ]
)

# %%
# Core department organisation-level EEI scores vs median HEO/SEO pay regression, for 2024 (morale data) and 2025 (pay data)
utils.draw_scatter_plot(
    df=df_pay_csps_dept,
    x_var="Median salary deflated",
    y_var=EEI_LABEL,
    height=3,
    hue="Organisation type",
    best_fit=True,
    fit_reg=False,
)

utils.fit_regressions(
    df_pay_csps_dept, x_vars=["Median salary deflated"], y_var=EEI_LABEL, data_description="2024 organisation-level data, depts only"
)

# %%
# Core department organisation-level EEI scores vs median HEO/SEO pay two-way fixed effects regression
utils.fit_fixed_effects_regression(
    df_pay_csps_dept_panel,
    x_var="Median salary deflated",
    y_var=EEI_LABEL,
    entity_var="Organisation",
    time_var="Year",
    data_description="Organisation-level panel data, depts only"
)

# %%
# Core department organisation-level pay and benefits theme scores vs median HEO/SEO pay regression, for 2024 (morale data) and 2025 (pay data)
utils.draw_scatter_plot(
    df=df_pay_csps_dept,
    x_var="Median salary deflated",
    y_var="Pay and benefits",
    height=3,
    hue="Organisation type",
    best_fit=True,
    fit_reg=False,
)

utils.fit_regressions(
    df_pay_csps_dept, x_vars=["Median salary deflated"], y_var="Pay and benefits", data_description="2024 organisation-level data, depts only"
)

# %%
# Core department organisation-level pay and benefits theme scores vs median HEO/SEO pay two-way fixed effects regression
utils.fit_fixed_effects_regression(
    df_pay_csps_dept_panel,
    x_var="Median salary deflated",
    y_var="Pay and benefits",
    entity_var="Organisation",
    time_var="Year",
    data_description="Organisation-level panel data, depts only"
)

# %%
# Core department organisation-level HEO/SEO pay records with missing median salary
display(
    df_pay_csps_dept[
        df_pay_csps_dept["Median salary deflated"].isna()
    ]
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
