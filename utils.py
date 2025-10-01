import pandas as pd
import seaborn as sns
import statsmodels.api as sm


def check_csps_data(
    df: pd.DataFrame,
    csps_min_year: int,
    csps_max_year: int,
    csps_mean_min_year: int,
    dept_groups_to_drop: list[str],
    orgs_to_drop: list[str],
    dept_only_conditions: dict,
    csps_median_organisation_name: str,
    csps_mean_organisation_name: str,
    eei_label: str,
    ts_labels: list[str]
) -> None:
    """
    Run data validation checks on CSPS dataframe.

    Args:
        df: The CSPS organisation dataframe to validate
        csps_min_year: Minimum expected year in the data
        csps_max_year: Maximum expected year in the data
        csps_mean_min_year: Minimum year for which mean data should be available
        dept_groups_to_drop: List of departmental groups that should be present for dropping
        orgs_to_drop: List of organisations that should be present for dropping
        dept_only_conditions: Dictionary with organisation type and organisation filters for department analysis
        csps_median_organisation_name: Name of the median benchmark organisation
        csps_mean_organisation_name: Name of the mean benchmark organisation
        eei_label: Label for Employee Engagement Index
        ts_labels: List of theme score labels

    Raises:
        AssertionError: If any validation check fails
    """
    # Check that all years are present
    years_present = df["Year"].unique()
    years_missing = [year for year in range(csps_min_year, csps_max_year + 1) if year not in years_present]

    assert all(year in years_present for year in range(csps_min_year, csps_max_year + 1)), f"Not all years are present: {years_missing}"

    # Check that departmental groups we plan to drop are present
    dept_groups_present = df["Departmental group"].unique()
    dept_groups_missing = [group for group in dept_groups_to_drop if group not in dept_groups_present]

    assert len(dept_groups_missing) == 0, f"Some departmental groups to drop are not present: {dept_groups_missing}"

    # Check that organisations we plan to drop are present
    orgs_present = df["Organisation"].unique()
    orgs_missing = [org for org in orgs_to_drop if org not in orgs_present]

    assert len(orgs_missing) == 0, f"Some organisations to drop are not present: {orgs_missing}"

    # Check that organisation types and organisations we plan to use in the department-only analysis are present
    org_types_present = df["Organisation type"].unique()
    org_types_missing = [otype for otype in dept_only_conditions["organisation_type_filter"] if otype not in org_types_present]
    orgs_present = df["Organisation"].unique()
    orgs_missing = [org for org in dept_only_conditions["include_orgs"] + dept_only_conditions["exclude_orgs"] if org not in orgs_present]

    assert len(org_types_missing) == 0, f"Some organisation types for department-only analysis are not present: {org_types_missing}"
    assert len(orgs_missing) == 0, f"Some organisations for department-only analysis are not present: {orgs_missing}"

    # Check that median and mean figures are present for all years
    median_missing = []
    mean_missing = []

    for year in range(csps_min_year, csps_max_year + 1):
        df_year = df[df["Year"] == year]
        if csps_median_organisation_name not in df_year["Organisation"].values:
            median_missing.append(year)
        if year >= csps_mean_min_year:
            if csps_mean_organisation_name not in df_year["Organisation"].values:
                mean_missing.append(year)

    assert len(median_missing) == 0, f"Median missing for years: {median_missing}"
    assert len(mean_missing) == 0, f"Mean missing for years: {mean_missing}"

    # Check that EEI and theme score values are present for each year
    eei_ts_missing = {year: [] for year in range(csps_min_year, csps_max_year + 1)}

    for year in range(csps_min_year, csps_max_year + 1):
        df_year = df[df["Year"] == year]
        for label in [eei_label] + ts_labels:
            if label not in df_year["Label"].values:
                eei_ts_missing[year].append(label)
        if len(eei_ts_missing[year]) == 0:
            del eei_ts_missing[year]

    assert len(eei_ts_missing) == 0, f"EEI and theme scores missing for years: {eei_ts_missing}"


def check_pay_data(
    df: pd.DataFrame,
    pay_min_year: int,
    pay_max_year: int,
    dept_groups_to_drop: list[str],
    dept_only_conditions: dict,
    pay_summary_organisation_name: str,
    pay_summary_grade_name: str,
) -> None:
    """
    Run data validation checks on pay dataframe.

    Args:
        df: The pay dataframe to validate
        pay_min_year: Minimum expected year in the data
        pay_max_year: Maximum expected year in the data
        dept_groups_to_drop: List of departmental groups that should be present for dropping
        dept_only_conditions: Dictionary with organisation type and organisation filters for department analysis
        pay_summary_organisation_name: Name of the overall civil service summary organisation
        pay_summary_grade_name: Name of the overall civil service summary grade

    Raises:
        AssertionError: If any validation check fails

    Notes:
        Unlike check_csps_data, this function does need to check for any organisations that we will need to drop.
    """
    # Check that all years are present
    years_present = df["Year"].unique()
    years_missing = [year for year in range(pay_min_year, pay_max_year + 1) if year not in years_present]

    assert all(year in years_present for year in range(pay_min_year, pay_max_year + 1)), f"Not all years are present: {years_missing}"

    # Check that departmental groups we plan to drop are present
    dept_groups_present = df["Departmental group"].unique()
    dept_groups_missing = [group for group in dept_groups_to_drop if group not in dept_groups_present]

    assert len(dept_groups_missing) == 0, f"Some departmental groups to drop are not present: {dept_groups_missing}"

    # Check that organisation types and organisations we plan to use in the department-only analysis are present
    org_types_present = df["Organisation type"].unique()
    org_types_missing = [otype for otype in dept_only_conditions["organisation_type_filter"] if otype not in org_types_present]
    orgs_present = df["Organisation"].unique()
    orgs_missing = [org for org in dept_only_conditions["include_orgs"] + dept_only_conditions["exclude_orgs"] if org not in orgs_present]

    assert len(org_types_missing) == 0, f"Some organisation types for department-only analysis are not present: {org_types_missing}"
    assert len(orgs_missing) == 0, f"Some organisations for department-only analysis are not present: {orgs_missing}"

    # Check that overall figures are present for all years
    overall_missing = []

    for year in range(pay_min_year, pay_max_year + 1):
        df_year = df[df["Year"] == year]
        if pay_summary_organisation_name not in df_year["Organisation"].values:
            overall_missing.append(year)

    assert len(overall_missing) == 0, f"Overall figures missing for years: {overall_missing}"

    # Check that 'All employees' Grade values are present for each year
    grade_missing = {year: [] for year in range(pay_min_year, pay_max_year + 1)}

    for year in range(pay_min_year, pay_max_year + 1):
        df_year = df[df["Year"] == year]
        if pay_summary_grade_name not in df_year["Grade"].values:
            grade_missing[year].append(pay_summary_grade_name)
        if len(grade_missing[year]) == 0:
            del grade_missing[year]

    assert len(grade_missing) == 0, f"'{pay_summary_grade_name}' Grade missing for years: {grade_missing}"


def edit_csps_data(
    df: pd.DataFrame,
    dept_groups_to_drop: list[str],
    orgs_to_drop: list[str],
    min_year: int = None,
    max_year: int = None
) -> pd.DataFrame:
    """
    Apply data transformations and cleaning to CSPS dataframe.

    Args:
        df: The raw CSPS organisation dataframe
        dept_groups_to_drop: List of departmental groups to exclude
        orgs_to_drop: List of organisations to exclude to avoid double-counting
        min_year: Minimum year to include (optional)
        max_year: Maximum year to include (optional)

    Returns:
        pd.DataFrame: Cleaned and processed dataframe with EEI and theme scores only
    """
    # Restrict to EEI and theme scores
    df_processed = df.loc[
        (df["Section"] == "Employee Engagement Index") |
        (df["Section"] == "Theme scores")
    ].copy()

    # Convert 'Year' column to integer
    df_processed["Year"] = df_processed["Year"].astype(int)

    # Convert 'Value' column to numeric
    df_processed["Value"] = pd.to_numeric(df_processed["Value"])

    # Restrict to specified year range
    if min_year is not None:
        df_processed = df_processed[df_processed["Year"] >= min_year]
    if max_year is not None:
        df_processed = df_processed[df_processed["Year"] <= max_year]

    # Drop departmental groups we're not interested in
    df_processed = df_processed[
        ~df_processed["Departmental group"].isin(dept_groups_to_drop)
    ]

    # Drop organisations that would introduce double-counting
    df_processed = df_processed[
        ~df_processed["Organisation"].isin(orgs_to_drop)
    ]

    return df_processed


def edit_pay_data(
    df: pd.DataFrame,
    dept_groups_to_drop: list[str],
    min_year: int = None,
    max_year: int = None
) -> pd.DataFrame:
    """
    Apply data transformations and cleaning to pay dataframe.

    Args:
        df: The raw pay dataframe
        dept_groups_to_drop: List of departmental groups to exclude
        min_year: Minimum year to include (optional)
        max_year: Maximum year to include (optional)

    Returns:
        pd.DataFrame: Cleaned and processed pay dataframe

    Notes:
        Unlike edit_csps_data, this function does not need to drop any organisations to avoid double-counting.
    """
    # Restrict to 'All employees' Grade
    df_processed = df[df["Grade"] == "All employees"].copy()

    # Convert 'Year' column to integer
    df_processed["Year"] = df_processed["Year"].astype(int)

    # Convert 'Median salary' column to numeric
    df_processed["Median salary"] = pd.to_numeric(df_processed["Median salary"])

    # Restrict to specified year range
    if min_year is not None:
        df_processed = df_processed[df_processed["Year"] >= min_year]
    if max_year is not None:
        df_processed = df_processed[df_processed["Year"] <= max_year]

    # Drop departmental groups we're not interested in
    df_processed = df_processed[
        ~df_processed["Departmental group"].isin(dept_groups_to_drop)
    ]

    return df_processed


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


def draw_1d_pairplot(df: pd.DataFrame, x_vars: list[str], y_var: str, hue: str = None, palette: str = None) -> sns.axisgrid.PairGrid:
    """
    Create n x 1 array of scatter plots, showing EEI score versus each theme score with lines of best fit.

    Args:
        df: DataFrame with data in wide format (measures in individual columns)
        x_vars: Measures to use as x variables
        y_var: Measure to use as y variable
        hue: Column name to use for colour coding (optional)

    Returns:
        seaborn PairGrid object
    """
    # When using hue, create scatter plots first, then add regression line manually
    if hue is not None:
        g = sns.pairplot(
            df,
            kind="scatter",
            diag_kind=None,
            x_vars=x_vars,
            y_vars=[y_var],
            hue=hue,
            palette=palette,
            plot_kws={"alpha": 0.7, "s": 50}
        )

        # Add regression lines manually
        for i, theme in enumerate(x_vars):
            ax = g.axes[0, i]
            sns.regplot(
                data=df,
                x=theme,
                y=y_var,
                ax=ax,
                scatter=False,
                line_kws={"color": "#333F48", "alpha": 0.5},
                ci=None
            )

        return g

    # Original behaviour for non-hue case
    else:
        return sns.pairplot(
            df,
            kind="reg",
            plot_kws={"ci": None, "scatter_kws": {"alpha": 0.5}, "line_kws": {"linewidth": 1.5}},
            diag_kind=None,
            x_vars=x_vars,
            y_vars=[y_var],
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
