# %%
"""
    Purpose
        Analyse CSPS theme scores by organisation. Analyses four things:
            - Organisation-level EEI and theme scores for 2024
            - Ministerial department organisation-level EEI and theme scores for 2024
            - CS mean EEI and theme scores over time
            - CS median EEI and theme scores over time
    Inputs
        - XLSX: "Organisation working file.xlsx"
            - CSPS organisation data
    Outputs
        None
    Notes
        - Scottish and Welsh organisations are dropped, but this will only apply to organisation-level analysis and not analysis based on all-organisation averages
        - Two organisations are dropped to avoid double-counting:
            - Ministry of Justice group (including agencies): Dropped as 'Ministry of Justice' (i.e. the core department) exists as a separate organisation in the data
            - UK Statistics Authority (excluding Office for National Statistics): Dropped as 'UK Statistics Authority' exists as a separate organisation in the data and includes the ONS. ONS is a sub-unit rather than a distinct organisation, therefore we want to include it
        - DfE figures included in this analysis are group figures, unlike other ministerial departments (see Excel working file for further details)
"""

import os

from IPython.display import display
import pandas as pd
import seaborn as sns
import statsmodels.api as sm

# %%
# SET CONSTANTS
CSPS_ORGANISATION_PATH = "C:/Users/" + os.getlogin() + "/Institute for Government/Data - General/Civil service/Civil Service - People Survey/"
CSPS_ORGANISATION_FILE_NAME = "Organisation working file.xlsx"
CSPS_ORGANISATION_SHEET = "Data.Collated"

MEDIAN_ORGANISATION_NAME = "Civil Service benchmark"
MEAN_ORGANISATION_NAME = "All employees"

MIN_YEAR = 2010
MAX_YEAR = 2024
MEAN_MIN_YEAR = 2019

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
    "UK Statistics Authority (excluding Office for National Statistics)",
]

# %%
# LOAD DATA
df_csps_organisation = pd.read_excel(CSPS_ORGANISATION_PATH + CSPS_ORGANISATION_FILE_NAME, sheet_name=CSPS_ORGANISATION_SHEET)

# %%
# EDIT DATA
# Restrict to EEI and theme scores
df_csps_organisation_eei_ts = df_csps_organisation.loc[
    (df_csps_organisation["Section"] == "Employee Engagement Index") |
    (df_csps_organisation["Section"] == "Theme scores")
].copy()

# %%
# Convert 'Value' column to numeric
df_csps_organisation_eei_ts["Value"] = pd.to_numeric(df_csps_organisation_eei_ts["Value"])

# %%
# Drop departmental groups we're not interested in
df_csps_organisation_eei_ts = df_csps_organisation_eei_ts[
    ~df_csps_organisation_eei_ts["Departmental group"].isin(DEPT_GROUPS_TO_DROP)
]

# %%
# Drop organisations that would introduce double-counting
df_csps_organisation_eei_ts = df_csps_organisation_eei_ts[
    ~df_csps_organisation_eei_ts["Organisation"].isin(ORGS_TO_DROP)
]

# %%
# Check that all years are present
years_present = df_csps_organisation_eei_ts["Year"].unique()
years_missing = [year for year in range(MIN_YEAR, MAX_YEAR + 1) if year not in years_present]

assert all(year in years_present for year in range(MIN_YEAR, MAX_YEAR + 1)), f"Not all years are present: {years_missing}"

# %%
# Check that median and mean figures are present for all years
median_missing = []
mean_missing = []

for year in range(MIN_YEAR, MAX_YEAR + 1):
    df_year = df_csps_organisation_eei_ts[df_csps_organisation_eei_ts["Year"] == year]
    if MEDIAN_ORGANISATION_NAME not in df_year["Organisation"].values:
        median_missing.append(year)
    if year >= MEAN_MIN_YEAR:
        if MEAN_ORGANISATION_NAME not in df_year["Organisation"].values:
            mean_missing.append(year)

assert len(median_missing) == 0, f"Median missing for years: {median_missing}"
assert len(mean_missing) == 0, f"Mean missing for years: {mean_missing}"

# %%
# Check that EEI and theme score values are as expected for each year
eei_ts_missing = {year: [] for year in range(MIN_YEAR, MAX_YEAR + 1)}

for year in range(MIN_YEAR, MAX_YEAR + 1):
    df_year = df_csps_organisation_eei_ts[df_csps_organisation_eei_ts["Year"] == year]
    for label in [EEI_LABEL] + TS_LABELS:
        if label not in df_year["Label"].values:
            eei_ts_missing[year].append(label)
    if len(eei_ts_missing[year]) == 0:
        del eei_ts_missing[year]

assert len(eei_ts_missing) == 0, f"EEI and theme scores missing for years: {eei_ts_missing}"


# %%
# DEFINE FUNCTIONS
def filter_and_pivot_data(df, organisation_filter=None, year_filter=None, exclude_orgs=None):
    """
    Filter CSPS data by organisation and/or year, then create a pivot table.

    Args:
        df: DataFrame containing CSPS data
        organisation_filter: String or list of organisation names to include (optional)
        year_filter: Year or list of years to include (optional)
        exclude_orgs: List of organisation names to exclude (optional)
        eei_label: Employee Engagement Index label
        ts_labels: List of theme score labels

    Returns:
        DataFrame with pivoted data (Organisation/Year as index, Labels as columns)
    """
    df_filtered = df.copy()

    # Apply organisation filter
    if organisation_filter is not None:
        if isinstance(organisation_filter, str):
            df_filtered = df_filtered[df_filtered["Organisation"] == organisation_filter]
        else:
            df_filtered = df_filtered[df_filtered["Organisation"].isin(organisation_filter)]

    # Apply year filter
    if year_filter is not None:
        if isinstance(year_filter, (int, float)):
            df_filtered = df_filtered[df_filtered["Year"] == year_filter]
        else:
            df_filtered = df_filtered[df_filtered["Year"].isin(year_filter)]

    # Exclude organisations
    if exclude_orgs is not None:
        df_filtered = df_filtered[~df_filtered["Organisation"].isin(exclude_orgs)]

    # Create pivot table

    # Single organisation over time
    if organisation_filter is not None and year_filter is None:
        df_pivot = df_filtered.pivot_table(
            index=["Year"], columns="Label", values="Value"
        ).reset_index()
    # Multiple organisations in a specific year
    elif organisation_filter is None and year_filter is not None:
        df_pivot = df_filtered.pivot_table(
            index=["Organisation"], columns="Label", values="Value"
        ).reset_index()

    return df_pivot


def create_eei_theme_pairplot(df_pivot, eei_label, ts_labels):
    """
    Create n x 1 array of scatter plots, showing EEI score versus each theme score.

    Args:
        df_pivot: DataFrame with pivoted data
        eei_label: Employee Engagement Index column name
        ts_labels: List of theme score column names

    Returns:
        seaborn PairGrid object
    """
    return sns.pairplot(
        df_pivot,
        plot_kws={"alpha": 0.5},
        x_vars=ts_labels,
        y_vars=[eei_label]
    )


def calculate_eei_theme_correlations(df_pivot, eei_label, ts_labels):
    """
    Calculate correlation matrix for EEI and theme scores.

    Args:
        df_pivot: DataFrame with pivoted data
        eei_label: Employee Engagement Index column name
        ts_labels: List of theme score column names

    Returns:
        DataFrame with correlation matrix (EEI row, theme score columns)
    """
    # Create correlation matrix
    # NB: Supplying the first value to .loc[] as a list ensures the result is a DataFrame, not a Series
    corr_matrix = df_pivot.corr(numeric_only=True)
    return corr_matrix.loc[[eei_label], ts_labels]


def fit_eei_theme_regressions(df_pivot, eei_label, ts_labels, data_description, year_filter=None):
    """
    Fit regression models of EEI against each theme score and print results.

    Args:
        df_pivot: DataFrame with pivoted data
        eei_label: Employee Engagement Index column name
        ts_labels: List of theme score column names
        data_description: String describing the data for output labels
        year_filter: Optional year to filter data (for time series data)
    """
    df_analysis = df_pivot.copy()

    # Filter by year if specified (for time series data)
    if year_filter is not None and "Year" in df_analysis.columns:
        df_analysis = df_analysis[df_analysis["Year"] == year_filter]

    for theme in ts_labels:
        if len(df_analysis) < 2:
            print(f"Insufficient data for regression: EEI vs {theme} ({data_description})")
            continue

        X = df_analysis[theme]
        y = df_analysis[eei_label]

        # Remove any NaN values
        mask = ~(X.isna() | y.isna())
        X = X[mask]
        y = y[mask]

        if len(X) < 2:
            print(f"Insufficient valid data for regression: EEI vs {theme} ({data_description})")
            continue

        # Add constant term for intercept
        X_with_const = sm.add_constant(X)

        # Fit OLS regression model
        model = sm.OLS(y, X_with_const).fit()

        # Extract key statistics
        r_squared = model.rsquared
        p_value = model.f_pvalue
        intercept = model.params.iloc[0]
        slope = model.params.iloc[1]

        print(f"Regression results for EEI vs {theme} ({data_description}):")
        print(f"  R-squared: {r_squared:.4f}")
        print(f"  P-value: {p_value:.4e}")
        print(f"  Equation: EEI = {intercept:.4f} + {slope:.4f} * {theme}")
        print()


# %%
# ANALYSE DATA
# Organisation-level EEI and theme scores for 2024
df_csps_organisation_eei_ts_2024_noavgs_pivot = filter_and_pivot_data(
    df_csps_organisation_eei_ts,
    year_filter=2024,
    exclude_orgs=[MEDIAN_ORGANISATION_NAME, MEAN_ORGANISATION_NAME],
)

create_eei_theme_pairplot(df_csps_organisation_eei_ts_2024_noavgs_pivot, EEI_LABEL, TS_LABELS)

df_csps_organisation_eei_ts_2024_noavgs_corr = calculate_eei_theme_correlations(
    df_csps_organisation_eei_ts_2024_noavgs_pivot, EEI_LABEL, TS_LABELS
)
display(df_csps_organisation_eei_ts_2024_noavgs_corr)

fit_eei_theme_regressions(
    df_csps_organisation_eei_ts_2024_noavgs_pivot, EEI_LABEL, TS_LABELS, "2024 organisation-level data"
)

# %%
# CS mean EEI and theme scores over time
df_csps_organisation_eei_ts_mean_pivot = filter_and_pivot_data(
    df_csps_organisation_eei_ts,
    organisation_filter=MEAN_ORGANISATION_NAME,
)

create_eei_theme_pairplot(df_csps_organisation_eei_ts_mean_pivot, EEI_LABEL, TS_LABELS)

df_csps_organisation_eei_ts_mean_corr = calculate_eei_theme_correlations(
    df_csps_organisation_eei_ts_mean_pivot, EEI_LABEL, TS_LABELS
)
display(df_csps_organisation_eei_ts_mean_corr)

fit_eei_theme_regressions(
    df_csps_organisation_eei_ts_mean_pivot, EEI_LABEL, TS_LABELS, "2024 mean data", year_filter=2024
)

# %%
# CS median EEI and theme scores over time
df_csps_organisation_eei_ts_median_pivot = filter_and_pivot_data(
    df_csps_organisation_eei_ts,
    organisation_filter=MEDIAN_ORGANISATION_NAME,
)

create_eei_theme_pairplot(df_csps_organisation_eei_ts_median_pivot, EEI_LABEL, TS_LABELS)

df_csps_organisation_eei_ts_median_corr = calculate_eei_theme_correlations(
    df_csps_organisation_eei_ts_median_pivot, EEI_LABEL, TS_LABELS
)
display(df_csps_organisation_eei_ts_median_corr)

fit_eei_theme_regressions(
    df_csps_organisation_eei_ts_median_pivot, EEI_LABEL, TS_LABELS, "2024 median data", year_filter=2024
)

# %%
