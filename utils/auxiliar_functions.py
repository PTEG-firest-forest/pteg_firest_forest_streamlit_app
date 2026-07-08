import pandas as pd

def df_climate_values(df_resumen, yyyy, Q, values_list_column_name='Values_List'):
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
    fila = df_resumen[(df_resumen['Year'] == yyyy) & (df_resumen['Quarter'] == Q)]
    if not fila.empty:
        valores = fila[values_list_column_name].iloc[0]
        return pd.DataFrame({f'Climate_Values_Q{Q}_{yyyy}': valores})
    else:
        # The original code had a print statement here, but since this function might be called
        # repeatedly in loops, it might lead to excessive output.
        # The calling functions usually handle the case where the returned DataFrame is empty.
        # print(f"No se encontraron datos para el Año {yyyy}, Trimestre {Q} en la columna '{values_list_column_name}'.")
        return pd.DataFrame() # Return an empty DataFrame if no data
    

def analyze_climate_by_quarter(df_input, climate_variable_column_name='temperature_2m_mean_(C)'):
    """
    Analyzes a specified climate variable by year and quarter, calculating the mean
    and providing a list of all values for each group.

    Args:
        df_input (pd.DataFrame): A DataFrame processed by split_climate_data_by_window,
                                 containing 'acq_date' and the specified climate variable column.
        climate_variable_column_name (str): The name of the climate variable column to analyze.
                                            Defaults to 'temperature_2m_mean_(C)'.

    Returns:
        pd.DataFrame: A DataFrame summarized by year and quarter with mean and
                      a list of climate variable values.
    """
    if df_input.empty:
        print("Input DataFrame is empty. Returning an empty DataFrame.")
        return pd.DataFrame()

    df_copy = df_input.copy() # Make a copy here to prevent modifying original df_input

    # Ensure acq_date is datetime
    df_copy['acq_date'] = pd.to_datetime(df_copy['acq_date'])

    # Extract year and quarter
    df_copy['Year'] = df_copy['acq_date'].dt.year
    df_copy['Quarter'] = df_copy['acq_date'].dt.quarter

    # Ensure climate variable column exists
    if climate_variable_column_name not in df_copy.columns:
        print(f"Error: '{climate_variable_column_name}' column not found in the input DataFrame.")
        return pd.DataFrame()

    # Convert the climate variable column to numeric, coercing errors to NaN
    df_copy[climate_variable_column_name] = pd.to_numeric(df_copy[climate_variable_column_name], errors='coerce')

    # Drop rows where the climate variable is NaN after conversion
    initial_len = len(df_copy)
    df_copy.dropna(subset=[climate_variable_column_name], inplace=True)
    if len(df_copy) < initial_len:
        print(f"Dropped {initial_len - len(df_copy)} rows due to invalid or missing values in '{climate_variable_column_name}'.")

    if df_copy.empty:
        print(f"No valid numeric data remaining for '{climate_variable_column_name}' after dropping NaNs. Returning empty DataFrame.")
        return pd.DataFrame()

    # Group by Year and Quarter, then aggregate
    df_resumen = df_copy.groupby(['Year', 'Quarter']).agg(
        Mean_Value=(climate_variable_column_name, 'mean'),
        Values_List=(climate_variable_column_name, list)
    ).reset_index()

    # Sort by Quarter and then by Year
    df_resumen = df_resumen.sort_values(by=['Quarter', 'Year']).reset_index(drop=True)

    # Round the main mean temperature
    df_resumen['Mean_Value'] = df_resumen['Mean_Value'].round(6)

    # (Optional) Round also the numbers within the list for easier reading
    df_resumen['Values_List'] = df_resumen['Values_List'].apply(lambda x: [round(i, 6) for i in x])

    return df_resumen

