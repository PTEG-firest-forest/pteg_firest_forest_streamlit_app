import pandas as pd
from scipy import stats

from .auxiliar_functions import analyze_climate_by_quarter


def df_climate_values(df_resumen, yyyy, Q, values_list_column_name="Values_List"):
    """
    Extracts the list of climate values for a specific year and quarter
    from a summarized climate DataFrame.

    Args:
        df_resumen (pd.DataFrame): The DataFrame containing summarized climate data
                                    with 'Year', 'Quarter', and a column specified by values_list_column_name.
        yyyy (int): The target year.
        Q (int): The target quarter.
        values_list_column_name (str): The name of the column in df_resumen that contains the list of values.

    Returns:
        pd.DataFrame: A DataFrame with a single column containing the climate values,
                      or an empty DataFrame if no data is found.
    """
    fila = df_resumen[(df_resumen["Year"] == yyyy) & (df_resumen["Quarter"] == Q)]
    if not fila.empty:
        valores = fila[values_list_column_name].iloc[0]
        return pd.DataFrame({f"Climate_Values_Q{Q}_{yyyy}": valores})
    else:
        # The original code had a print statement here, but since this function might be called
        # repeatedly in loops, it might lead to excessive output.
        # The calling functions usually handle the case where the returned DataFrame is empty.
        # print(f"No se encontraron datos para el Año {yyyy}, Trimestre {Q} en la columna '{values_list_column_name}'.")
        return pd.DataFrame()  # Return an empty DataFrame if no data


def perform_quarterly_climate_anova(
    df_resumen,
    year,
    climate_variable_column_name="temperature_2m_mean_(C)",
    values_list_column_name="Values_List",
    verbose=True,
):
    """
    Performs a one-way ANOVA test on climate values across the four quarters of a given year.

    Args:
        df_resumen (pd.DataFrame): The DataFrame containing summarized climate data
                                        with 'Year', 'Quarter', and the specified values_list_column_name.
        year (int): The target year for the ANOVA test.
        climate_variable_column_name (str): The name of the climate variable column used for context in messages.
        values_list_column_name (str): The name of the column in df_resumen that contains the list of values.
        verbose (bool): If True, prints detailed results; otherwise, returns only the statistic and p-value.
    """
    if verbose:
        print(
            f"\n--- Performing ANOVA test for year {year} on {climate_variable_column_name} ---"
        )

    quarter_data = {}
    all_quarters_empty = True

    for Q in range(1, 5):
        df_q_values = df_climate_values(
            df_resumen, year, Q, values_list_column_name=values_list_column_name
        )
        if not df_q_values.empty:
            # Get the dynamic column name, e.g., 'Climate_Values_Q1_2014'
            climate_col_name = df_q_values.columns[0]
            quarter_data[f"Q{Q}"] = df_q_values[climate_col_name].tolist()
            all_quarters_empty = False
        else:
            if verbose:
                print(
                    f"Warning: No {climate_variable_column_name} data found for {year}-Q{Q}. This quarter will be excluded from ANOVA."
                )

    if (
        all_quarters_empty or len(quarter_data) < 2
    ):  # ANOVA requires at least two groups
        if verbose:
            print(
                f"Not enough data to perform ANOVA for year {year} on {climate_variable_column_name}. Need at least two quarters with data."
            )
        return None, None  # Return None, None if ANOVA cannot be performed

    # Prepare data for ANOVA, ensuring only non-empty lists are passed
    anova_groups = [data for data in quarter_data.values() if data]

    if len(anova_groups) < 2:
        if verbose:
            print(
                f"Not enough complete quarters to perform ANOVA for year {year} on {climate_variable_column_name}."
            )
        return None, None  # Return None, None if ANOVA cannot be performed

    # Perform the ANOVA test
    f_statistic, p_value = stats.f_oneway(*anova_groups)

    if verbose:
        print(f"F-statistic: {f_statistic:.4f}")
        print(f"p-value: {p_value:.4f}")

        # Interpret the results
        alfa = 0.05
        if p_value < alfa:
            print(
                f"Dado que el p-value ({p_value:.4f}) es menor que el nivel de significancia alfa ({alfa}),"
            )
            print(
                f"rechazamos la hipótesis nula. Esto sugiere que existen diferencias significativas en los valores medios de {climate_variable_column_name} entre al menos dos de los trimestres del año {year}."
            )
        else:
            print(
                f"Dado que el p-value ({p_value:.4f}) es mayor que el nivel de significancia alfa ({alfa}),"
            )
            print(
                f"no tenemos suficiente evidencia para rechazar la hipótesis nula. Esto sugiere que no hay diferencias significativas en los valores medios de {climate_variable_column_name} entre los trimestres del año {year}."
            )

    return f_statistic, p_value


def generate_yearly_anova_p_value_table(
    df_on_day_5,
    df_on_day_10,
    df_on_day_15,
    climate_variable_column_name="temperature_2m_mean_(C)",
    values_list_column_name="Values_List",
):
    """
    Generates a DataFrame comparing ANOVA p-values for each year across different sampling percentages.
    The p-value indicates if there are significant differences in mean of the specified climate variable
    between quarters *within* a given year for that sampling percentage.

    Args:
        df_on_day_5 (pd.DataFrame): DataFrame for 5% sampling (on_day data).
        df_on_day_10 (pd.DataFrame): DataFrame for 10% sampling (on_day data).
        df_on_day_15 (pd.DataFrame): DataFrame for 15% sampling (on_day data).
        climate_variable_column_name (str): The name of the climate variable column to analyze.
        values_list_column_name (str): The name of the column in df_resumen that contains the list of values.

    Returns:
        pd.DataFrame: A DataFrame with years as rows and sampling percentages as columns,
                      containing the ANOVA p-values.
    """
    print(
        f"Summarizing data for each sampling percentage for {climate_variable_column_name}..."
    )
    df_resumen_5 = analyze_climate_by_quarter(
        df_on_day_5, climate_variable_column_name=climate_variable_column_name
    )
    df_resumen_10 = analyze_climate_by_quarter(
        df_on_day_10, climate_variable_column_name=climate_variable_column_name
    )
    df_resumen_15 = analyze_climate_by_quarter(
        df_on_day_15, climate_variable_column_name=climate_variable_column_name
    )

    all_years = sorted(
        pd.concat(
            [df_resumen_5["Year"], df_resumen_10["Year"], df_resumen_15["Year"]]
        ).unique()
    )

    results = []

    print(
        f"\nCalculating ANOVA p-values for each year and sampling percentage for {climate_variable_column_name}..."
    )
    for year in all_years:
        row_data = {"year": year}

        # 5% Sampling
        _, p_value_5 = perform_quarterly_climate_anova(
            df_resumen_5,
            year,
            climate_variable_column_name=climate_variable_column_name,
            values_list_column_name=values_list_column_name,
            verbose=False,
        )
        row_data["5%"] = round(p_value_5, 6) if p_value_5 is not None else None

        # 10% Sampling
        _, p_value_10 = perform_quarterly_climate_anova(
            df_resumen_10,
            year,
            climate_variable_column_name=climate_variable_column_name,
            values_list_column_name=values_list_column_name,
            verbose=False,
        )
        row_data["10%"] = round(p_value_10, 6) if p_value_10 is not None else None

        # 15% Sampling
        _, p_value_15 = perform_quarterly_climate_anova(
            df_resumen_15,
            year,
            climate_variable_column_name=climate_variable_column_name,
            values_list_column_name=values_list_column_name,
            verbose=False,
        )
        row_data["15%"] = round(p_value_15, 6) if p_value_15 is not None else None

        results.append(row_data)

    df_anova_p_values = pd.DataFrame(results)
    print(
        f"Yearly ANOVA p-value table for {climate_variable_column_name} generated successfully."
    )
    return df_anova_p_values


def perform_quarterly_climate_ttest(
    df_resumen,
    year1,
    year2,
    quarter,
    climate_variable_column_name="temperature_2m_mean_(C)",
    values_list_column_name="Values_List",
):
    """
    Performs an independent two-sample t-test on climate values for a specific
    quarter across two different years.

    Args:
        df_resumen (pd.DataFrame): The DataFrame containing summarized climate data
                                        with 'Year', 'Quarter', and the specified values_list_column_name.
        year1 (int): The first target year for the t-test.
        year2 (int): The second target year for the t-test.
        quarter (int): The target quarter (1, 2, 3, or 4).
        climate_variable_column_name (str): The name of the climate variable column for contextual messages.
        values_list_column_name (str): The name of the column in df_resumen that contains the list of values.
    """
    print(
        f"\n--- Performing independent t-test for Quarter {quarter} on {climate_variable_column_name} between year {year1} and year {year2} ---"
    )

    # Get climate values for year1 and quarter
    df_q1_values = df_climate_values(
        df_resumen, year1, quarter, values_list_column_name=values_list_column_name
    )
    if df_q1_values.empty:
        print(
            f"Error: No {climate_variable_column_name} data found for Quarter {quarter} in Year {year1}. Cannot perform t-test."
        )
        return None, None
    climate_col_name_y1 = df_q1_values.columns[0]
    data_year1 = df_q1_values[climate_col_name_y1].tolist()

    # Get climate values for year2 and quarter
    df_q2_values = df_climate_values(
        df_resumen, year2, quarter, values_list_column_name=values_list_column_name
    )
    if df_q2_values.empty:
        print(
            f"Error: No {climate_variable_column_name} data found for Quarter {quarter} in Year {year2}. Cannot perform t-test."
        )
        return None, None
    climate_col_name_y2 = df_q2_values.columns[0]
    data_year2 = df_q2_values[climate_col_name_y2].tolist()

    if not data_year1 or not data_year2:
        print("Not enough data in one or both groups to perform t-test. Skipping.")
        return None, None

    # Perform independent two-sample t-test
    # We assume unequal variances (Welch's t-test) which is generally safer
    t_statistic, p_value = stats.ttest_ind(data_year1, data_year2, equal_var=False)

    print(f"T-statistic: {t_statistic:.4f}")
    print(f"P-value: {p_value:.4f}")

    # Interpret the results
    alfa = 0.05
    if p_value < alfa:
        print(
            f"Dado que el p-value ({p_value:.4f}) es menor que el nivel de significancia alfa ({alfa}),"
        )
        print(
            f"rechazamos la hipótesis nula. Esto sugiere que existen diferencias significativas en los valores medios de {climate_variable_column_name} entre el Año {year1} y el Año {year2} para el Trimestre {quarter}."
        )
    else:
        print(
            f"Dado que el p-value ({p_value:.4f}) es mayor que el nivel de significancia alfa ({alfa}),"
        )
        print(
            f"no tenemos suficiente evidencia para rechazar la hipótesis nula. Esto sugiere que no hay diferencias significativas en los valores medios de {climate_variable_column_name} entre el Año {year1} y el Año {year2} para el Trimestre {quarter}."
        )

    return t_statistic, p_value


def perform_quarterly_climate_comparison_test(
    df_resumen,
    years_list,
    quarter,
    climate_variable_column_name="temperature_2m_mean_(C)",
    values_list_column_name="Values_List",
    verbose=True,
):
    """
    Performs a t-test (for two years) or ANOVA (for more than two years)
    on a specified climate variable for a specific quarter.

    Args:
        df_resumen (pd.DataFrame): The DataFrame containing summarized climate data
                                        with 'Year', 'Quarter', and the specified values_list_column_name.
        years_list (list): A list of years to compare.
        quarter (int): The target quarter (1, 2, 3, or 4).
        climate_variable_column_name (str): The name of the climate variable column to analyze.
        values_list_column_name (str): The name of the column in df_resumen that contains the list of values.
        verbose (bool): If True, prints detailed results; otherwise, returns only the statistic and p-value.

    Returns:
        tuple: (statistic, p_value) or (None, None) if the test cannot be performed.
    """
    if verbose:
        print(
            f"\n--- Performing comparison test for Quarter {quarter} on {climate_variable_column_name} across years {years_list} ---"
        )

    # 1. Filter valid years (2014-2024)
    valid_years = [year for year in years_list if 2014 <= year <= 2024]
    valid_years = sorted(list(set(valid_years)))  # Remove duplicates and sort

    if not valid_years:
        if verbose:
            print(
                "Error: No valid years (between 2014 and 2024) provided for the test. Please check the input list."
            )
        return None, None

    if len(valid_years) == 1:
        if verbose:
            print(
                f"Error: Only one valid year ({valid_years[0]}) provided. Need at least two years for comparison."
            )
        return None, None

    if len(valid_years) == 2:
        year1, year2 = valid_years[0], valid_years[1]
        if verbose:
            print(
                f"Detected two valid years: {year1} and {year2}. Performing independent t-test."
            )

        # Get climate values for year1 and quarter
        df_q1_values = df_climate_values(
            df_resumen, year1, quarter, values_list_column_name=values_list_column_name
        )
        if df_q1_values.empty:
            if verbose:
                print(
                    f"Error: No {climate_variable_column_name} data found for Quarter {quarter} in Year {year1}. Cannot perform t-test."
                )
            return None, None
        data_year1 = df_q1_values.iloc[:, 0].tolist()

        # Get climate values for year2 and quarter
        df_q2_values = df_climate_values(
            df_resumen, year2, quarter, values_list_column_name=values_list_column_name
        )
        if df_q2_values.empty:
            if verbose:
                print(
                    f"Error: No {climate_variable_column_name} data found for Quarter {quarter} in Year {year2}. Cannot perform t-test."
                )
            return None, None
        data_year2 = df_q2_values.iloc[:, 0].tolist()

        if len(data_year1) < 2 or len(data_year2) < 2:
            if verbose:
                print(
                    f"Not enough data in one or both groups for Quarter {quarter} (Year {year1}: {len(data_year1)} samples, Year {year2}: {len(data_year2)} samples) to perform t-test. Skipping."
                )
            return None, None

        # Perform independent two-sample t-test
        t_statistic, p_value = stats.ttest_ind(data_year1, data_year2, equal_var=False)

        if verbose:
            print(f"T-statistic: {t_statistic:.4f}")
            print(f"P-value: {p_value:.4f}")
            # Interpret the results
            alfa = 0.05
            if p_value < alfa:
                print(
                    f"Dado que el p-value ({p_value:.4f}) es menor que el nivel de significancia alfa ({alfa}),"
                )
                print(
                    f"rechazamos la hipótesis nula. Esto sugiere que existen diferencias significativas en los valores medios de {climate_variable_column_name} entre el Año {year1} y el Año {year2} para el Trimestre {quarter}."
                )
            else:
                print(
                    f"Dado que el p-value ({p_value:.4f}) es mayor que el nivel de significancia alfa ({alfa}),"
                )
                print(
                    f"no tenemos suficiente evidencia para rechazar la hipótesis nula. Esto sugiere que no hay diferencias significativas en los valores medios de {climate_variable_column_name} entre el Año {year1} y el Año {year2} para el Trimestre {quarter}."
                )
        return t_statistic, p_value

    elif len(valid_years) > 2:
        if verbose:
            print(
                f"Detected {len(valid_years)} valid years: {valid_years}. Performing one-way ANOVA."
            )

        anova_groups = []
        missing_data_years = []

        for year in valid_years:
            df_q_values = df_climate_values(
                df_resumen,
                year,
                quarter,
                values_list_column_name=values_list_column_name,
            )
            if not df_q_values.empty:
                climate_col_name = df_q_values.columns[0]
                group_data = df_q_values[climate_col_name].tolist()
                if group_data:  # Ensure group data is not empty
                    anova_groups.append(group_data)
                else:
                    missing_data_years.append(year)
            else:
                missing_data_years.append(year)

        if missing_data_years and verbose:
            print(
                f"Warning: No {climate_variable_column_name} data found for Quarter {quarter} in year(s): {missing_data_years}. These years will be excluded from ANOVA."
            )

        if len(anova_groups) < 2:
            if verbose:
                print(
                    f"Not enough complete groups (years) to perform ANOVA. Need at least two years with data for the specified quarter for {climate_variable_column_name}."
                )
            return None, None

        # Perform the ANOVA test
        f_statistic, p_value = stats.f_oneway(*anova_groups)

        if verbose:
            print(f"F-statistic: {f_statistic:.4f}")
            print(f"P-value: {p_value:.4f}")

            # Interpret the results
            alfa = 0.05
            if p_value < alfa:
                print(
                    f"Dado que el p-value ({p_value:.4f}) es menor que el nivel de significancia alfa ({alfa}),"
                )
                print(
                    f"rechazamos la hipótesis nula. Esto sugiere que existen diferencias significativas en los valores medios de {climate_variable_column_name} entre al menos dos de los años ({', '.join(map(str, valid_years))}) para el Trimestre {quarter}."
                )
            else:
                print(
                    f"Dado que el p-value ({p_value:.4f}) es mayor que el nivel de significancia alfa ({alfa}),"
                )
                print(
                    f"no tenemos suficiente evidencia para rechazar la hipótesis nula. Esto sugiere que no hay diferencias significativas en los valores medios de {climate_variable_column_name} entre los años ({', '.join(map(str, valid_years))}) para el Trimestre {quarter}."
                )
        return f_statistic, p_value

    return None, None  # Should not be reached if logic is sound but added for safety
