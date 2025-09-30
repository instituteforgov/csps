# %%
"""
    Purpose
        Analyse CSPS theme scores by organisation. Analyses three things:
            - Organisation-level EEI and theme scores for 2024
            - Organisation-level EEI and theme scores for departments for 2024
            - CS median EEI and theme scores over time
    Inputs
        - XLSX: "Organisation working file.xlsx"
            - CSPS organisation data
    Outputs
        None
    Notes
        - Analysis is not carried out on CS mean figures, as there are insufficient data points: these are only available from 2019 onwards
        - Scottish and Welsh organisations are dropped, but this only applies to organisation-level analysis and not analysis based on the CS median
        - Three organisations are dropped to avoid double-counting:
            - 'Ministry of Justice group (including agencies)': Dropped as 'Ministry of Justice' (i.e. the core department) exists as a separate organisation in the data
            - 'Office for National Statistics' and 'UK Statistics Authority (excluding Office for National Statistics)': Dropped as 'UK Statistics Authority', which includes the ONS, exists as a separate organisation in the data. ONS is a sub-unit rather than a distinct organisation, therefore we want to include it as part of UKSA
        - DfE figures included in this analysis are group figures, unlike other ministerial departments (see Excel working file for further details)
        - The department-only analysis is carried out on ministerial departments plus HMRC and minus Export Credits Guarantee Department, for consistency with other Whitehall Monitor analysis
"""

import os

import pandas as pd
import seaborn as sns
import statsmodels.api as sm

from utils import check_csps_data, edit_csps_data

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
    "Office for National Statistics",
    "UK Statistics Authority (excluding Office for National Statistics)",
]

# NB: 'Organisations' that are dropped across all the organisation-level analysis - mean and median civil service figures - are intentionally not included here
DEPT_ONLY_CONDITIONS = {
    "organisation_type_filter": ["Ministerial department"],
    "exclude_orgs": ["Export Credits Guarantee Department"],
    "include_orgs": ["HM Revenue and Customs"],
}

# %%
# LOAD DATA
df_csps_organisation = pd.read_excel(CSPS_PATH + CSPS_FILE_NAME, sheet_name=CSPS_SHEET)

# %%
# RUN CHECKS ON DATA
check_csps_data(
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

# %%
# EDIT DATA
df_csps_organisation_eei_ts = edit_csps_data(
    df_csps_organisation,
    DEPT_GROUPS_TO_DROP,
    ORGS_TO_DROP
)


# %%
# DEFINE FUNCTIONS
def filter_pivot_data(
    df: pd.DataFrame,
    year_filter: int | float | list[int | float] | None = None,
    organisation_type_filter: str | list[str] | None = None,
    organisation_filter: str | list[str] | None = None,
    exclude_orgs: list[str] | None = None,
    include_orgs: list[str] | None = None,
    preserve_columns: list[str] | None = None
) -> pd.DataFrame:
    """
    Filter CSPS data by organisation and/or year, then create a pivot table.

    Args:
        df: DataFrame containing CSPS data
        year_filter: Year or list of years to include (optional)
        organisation_type_filter: String or list of organisation types to include (optional)
        organisation_filter: String or list of organisation names to include (optional)
        exclude_orgs: List of organisation names to exclude (optional)
        include_orgs: List of organisation names to include that would otherwise be excluded (optional)
        preserve_columns: List of additional columns to preserve in the pivot table (optional)

    Returns:
        DataFrame with pivoted data (Organisation/Year as index, Labels as columns, plus any preserved columns)

    Raises:
        TypeError: If df is not a pandas DataFrame
        ValueError: DataFrame is empty or no data remains after filtering
    """
    # Input validation
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    if df.empty:
        raise ValueError("DataFrame is empty")

    # Coerce filter arguments to lists
    if isinstance(year_filter, (int, float)):
        year_filter = [year_filter]

    if isinstance(organisation_type_filter, str):
        organisation_type_filter = [organisation_type_filter]

    if isinstance(organisation_filter, str):
        organisation_filter = [organisation_filter]

    if preserve_columns is None:
        preserve_columns = []

    # Create filtered copy
    df_filtered = df.copy()

    # Apply filters
    if year_filter is not None:
        df_filtered = df_filtered[df_filtered["Year"].isin(year_filter)]

    if organisation_type_filter is not None:
        df_filtered = df_filtered[
            (df_filtered["Organisation type"].isin(organisation_type_filter)) |
            (df_filtered["Organisation"].isin(include_orgs) if include_orgs else False)
        ]

    if organisation_filter is not None:
        df_filtered = df_filtered[
            df_filtered["Organisation"].isin(organisation_filter) |
            (df_filtered["Organisation"].isin(include_orgs) if include_orgs else False)
        ]

    if exclude_orgs:
        df_filtered = df_filtered[
            ~df_filtered["Organisation"].isin(exclude_orgs)
        ]

    if df_filtered.empty:
        raise ValueError("No data remains after applying filters")

    # Create pivot table
    # Single organisation over time
    if organisation_filter is not None and year_filter is None:
        df_pivot = df_filtered.pivot_table(
            index=["Year"] + preserve_columns, columns="Label", values="Value"
        ).reset_index()
    # Multiple organisations in a specific year
    elif organisation_filter is None and year_filter is not None:
        df_pivot = df_filtered.pivot_table(
            index=["Organisation"] + preserve_columns, columns="Label", values="Value"
        ).reset_index()
    else:
        # Handle edge case where both or neither filters are specified
        raise ValueError("Must specify either year_filter OR organisation_filter (but not both or neither)")

    return df_pivot


def create_eei_theme_pairplot(df_pivot: pd.DataFrame, eei_label: str, ts_labels: list[str], hue: str = None, palette: str = None) -> sns.axisgrid.PairGrid:
    """
    Create n x 1 array of scatter plots, showing EEI score versus each theme score with lines of best fit.

    Args:
        df_pivot: DataFrame with pivoted data
        eei_label: Employee Engagement Index column name
        ts_labels: List of theme score column names
        hue: Column name to use for colour coding (optional)

    Returns:
        seaborn PairGrid object
    """
    # When using hue, create scatter plots first, then add regression line manually
    if hue is not None:
        g = sns.pairplot(
            df_pivot,
            kind="scatter",
            diag_kind=None,
            x_vars=ts_labels,
            y_vars=[eei_label],
            hue=hue,
            palette=palette,
            plot_kws={"alpha": 0.7, "s": 50}
        )

        # Add regression lines manually
        for i, theme in enumerate(ts_labels):
            ax = g.axes[0, i]
            sns.regplot(
                data=df_pivot,
                x=theme,
                y=eei_label,
                ax=ax,
                scatter=False,
                line_kws={"color": "#333F48", "alpha": 0.5},
                ci=None
            )

        return g

    # Original behaviour for non-hue case
    else:
        return sns.pairplot(
            df_pivot,
            kind="reg",
            plot_kws={"ci": None, "scatter_kws": {"alpha": 0.5}, "line_kws": {"linewidth": 1.5}},
            diag_kind=None,
            x_vars=ts_labels,
            y_vars=[eei_label],
        )


def fit_eei_theme_regressions(df_pivot: pd.DataFrame, eei_label: str, ts_labels: list[str], data_description: str) -> None:
    """
    Fit regression models of EEI against each theme score and print results.

    Args:
        df_pivot: DataFrame with pivoted data
        eei_label: Employee Engagement Index column name
        ts_labels: List of theme score column names
        data_description: String describing the data for output labels
    """
    df_analysis = df_pivot.copy()

    def get_significance_stars(p_value: float) -> str:
        """Return asterisks based on p-value significance levels."""
        if p_value < 0.001:
            return "***"
        elif p_value < 0.01:
            return "**"
        elif p_value < 0.05:
            return "*"
        else:
            return ""

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

        # Get significance stars
        stars = get_significance_stars(p_value)

        print(f"Regression results for EEI vs {theme} ({data_description}):")
        print(f"  R²: {r_squared:.4f}")
        print(f"  p-value: {p_value:.4f}{stars}")
        print(f"  Equation: y = {intercept:.4f} + {slope:.4f}x")
        print()


# %%
# ANALYSE DATA
# Organisation-level EEI and theme scores for 2024
df_csps_organisation_eei_ts_2024_noavgs_pivot = filter_pivot_data(
    df_csps_organisation_eei_ts,
    year_filter=2024,
    exclude_orgs=[CSPS_MEDIAN_ORGANISATION_NAME, CSPS_MEAN_ORGANISATION_NAME],
    preserve_columns=["Organisation type"]
)

create_eei_theme_pairplot(df_csps_organisation_eei_ts_2024_noavgs_pivot, EEI_LABEL, TS_LABELS, hue="Organisation type")

fit_eei_theme_regressions(
    df_csps_organisation_eei_ts_2024_noavgs_pivot, EEI_LABEL, TS_LABELS, "2024 organisation-level data"
)

# %%
# Organisation-level EEI and theme scores for departments for 2024
df_csps_organisation_eei_ts_2024_depts_pivot = filter_pivot_data(
    df_csps_organisation_eei_ts,
    year_filter=2024,
    organisation_type_filter=DEPT_ONLY_CONDITIONS["organisation_type_filter"],
    exclude_orgs=[CSPS_MEDIAN_ORGANISATION_NAME, CSPS_MEAN_ORGANISATION_NAME] + DEPT_ONLY_CONDITIONS["exclude_orgs"],
    include_orgs=DEPT_ONLY_CONDITIONS["include_orgs"],
    preserve_columns=["Organisation type"]
)

create_eei_theme_pairplot(df_csps_organisation_eei_ts_2024_depts_pivot, EEI_LABEL, TS_LABELS, hue="Organisation type")

fit_eei_theme_regressions(
    df_csps_organisation_eei_ts_2024_depts_pivot, EEI_LABEL, TS_LABELS, "2024 organisation-level data, depts only"
)

# %%
# CS median EEI and theme scores over time
df_csps_organisation_eei_ts_median_pivot = filter_pivot_data(
    df_csps_organisation_eei_ts,
    organisation_filter=CSPS_MEDIAN_ORGANISATION_NAME,
)

create_eei_theme_pairplot(df_csps_organisation_eei_ts_median_pivot, EEI_LABEL, TS_LABELS, hue="Year", palette="rocket_r")

fit_eei_theme_regressions(
    df_csps_organisation_eei_ts_median_pivot, EEI_LABEL, TS_LABELS, "Civil service median data over time"
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
