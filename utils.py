import pandas as pd


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


def edit_csps_data(
    df: pd.DataFrame,
    dept_groups_to_drop: list[str],
    orgs_to_drop: list[str]
) -> pd.DataFrame:
    """
    Apply data transformations and cleaning to CSPS dataframe.

    Args:
        df: The raw CSPS organisation dataframe
        dept_groups_to_drop: List of departmental groups to exclude
        orgs_to_drop: List of organisations to exclude to avoid double-counting

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

    # Drop departmental groups we're not interested in
    df_processed = df_processed[
        ~df_processed["Departmental group"].isin(dept_groups_to_drop)
    ]

    # Drop organisations that would introduce double-counting
    df_processed = df_processed[
        ~df_processed["Organisation"].isin(orgs_to_drop)
    ]

    return df_processed
