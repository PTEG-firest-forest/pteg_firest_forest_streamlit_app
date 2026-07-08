import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd

from .test_functions import df_climate_values
from .auxiliar_functions import analyze_climate_by_quarter

def plot_climate_variable_with_variance(df_summary, climate_variable_column_name='temperature_2m_mean_(C)', values_list_column_name='Values_List', title_suffix="Evolución a lo largo del tiempo"):
    """
    Generates a line plot showing the mean of a specified climate variable and its variance (mean +/- 1 Std. Dev.)
    over time (Year-Quarter), and adds the number of records per quarter on a secondary axis.

    Args:
        df_summary (pd.DataFrame): A DataFrame containing summarized climate data
                                        with 'Year', 'Quarter', 'Mean_Value', and 'Values_List' columns.
        climate_variable_column_name (str): The name of the climate variable column being analyzed (for labels).
        values_list_column_name (str): The name of the column in df_summary that contains the list of values.
        title_suffix (str): A suffix for the plot title. The full title will be 'Mean of [variable name] + suffix'.
    """
    if df_summary.empty:
        print("Input DataFrame is empty. Cannot generate plot.")
        return

    # Make a copy to avoid modifying the original DataFrame passed in
    df_plot = df_summary.copy()

    # Create a combined 'YearQuarter' column for better visualization
    df_plot['YearQuarter'] = df_plot['Year'].astype(str) + '-Q' + df_plot['Quarter'].astype(str)

    # Ensure data is sorted by year and quarter
    df_plot = df_plot.sort_values(by=['Year', 'Quarter']).reset_index(drop=True)

    # Calculate the standard deviation of the specified values list for each quarter
    # Ensure there are lists to compute std from
    df_plot['Std_Dev'] = df_plot[values_list_column_name].apply(lambda x: np.std(x) if len(x) > 1 else np.nan)

    # Calculate the number of records for each quarter
    df_plot['Record_Count'] = df_plot[values_list_column_name].apply(len)

    fig, ax1 = plt.subplots(figsize=(18, 9))

    # Plot the mean climate variable on the primary y-axis (ax1)
    sns.lineplot(x='YearQuarter', y='Mean_Value', data=df_plot, marker='o', label=f'Promedio de {climate_variable_column_name}', ax=ax1, color='blue')

    # Plot fill_between for std dev only if there's enough data
    if not df_plot['Std_Dev'].isnull().all():
        ax1.fill_between(
            df_plot['YearQuarter'],
            df_plot['Mean_Value'] - df_plot['Std_Dev'],
            df_plot['Mean_Value'] + df_plot['Std_Dev'],
            color='blue', alpha=0.2, label=f'{climate_variable_column_name} ± 1 Std. Dev.'
        )

    ax1.set_xlabel('Año-Trimestre')
    ax1.set_ylabel(f'{climate_variable_column_name} Valores', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # Create a second y-axis (ax2) for the number of records
    ax2 = ax1.twinx()
    sns.lineplot(x='YearQuarter', y='Record_Count', data=df_plot, marker='o', label='Registros', ax=ax2, color='red')
    ax2.set_ylabel('Registros', color='red')
    ax2.tick_params(axis='y', labelcolor='red')

    plt.title(f'Promedio de {climate_variable_column_name} {title_suffix}')
    ax1.set_xticks(ax1.get_xticks())
    ax1.set_xticklabels(df_plot['YearQuarter'], rotation=90) # Rotate x-axis labels for readability
    ax1.grid(True, linestyle='--', alpha=0.7)

    # Combine legends from both axes
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper left')

    plt.tight_layout() # Adjust layout to prevent overlapping
    plt.show()






def plot_quarterly_climate_comparison(df_resumen, years_to_compare, climate_variable_column_name='temperature_2m_mean_(C)', values_list_column_name='Values_List'):
    """
    Generates box plots comparing the distribution of a specified climate variable across quarters
    for a specified list of years.

    Args:
        df_resumen (pd.DataFrame): The DataFrame containing summarized climate data
                                        with 'Year', 'Quarter', and the specified values_list_column_name.
        years_to_compare (list): A list of integer years for which to generate the comparison plots.
        climate_variable_column_name (str): The name of the climate variable column being analyzed (for labels).
        values_list_column_name (str): The name of the column in df_resumen that contains the list of values.
    """
    if df_resumen.empty:
        print("Input summary DataFrame is empty. Cannot generate plots.")
        return

    all_quarters_data = []

    for year in years_to_compare:
        for Q in range(1, 5): # Iterate through quarters 1 to 4
            df_quarter_values = df_climate_values(df_resumen, year, Q, values_list_column_name=values_list_column_name)

            if not df_quarter_values.empty:
                # Get the dynamic column name, e.g., 'Climate_Values_Q1_2014'
                climate_col_name_dynamic = df_quarter_values.columns[0]
                df_quarter_temp = df_quarter_values.rename(columns={climate_col_name_dynamic: 'Climate_Values'})
                df_quarter_temp['Quarter_Label'] = f'{year}-Q{Q}'
                all_quarters_data.append(df_quarter_temp)
            # else: print statement already handled by df_climate_values

    if not all_quarters_data:
        print(f"No {climate_variable_column_name} data found for the specified years and quarters: {years_to_compare}. Cannot generate plots.")
        return

    df_comparacion_anual = pd.concat(all_quarters_data)

    plt.figure(figsize=(12, 7))
    sns.boxplot(x='Quarter_Label', y='Climate_Values', data=df_comparacion_anual, hue='Quarter_Label', palette='viridis', legend=False)
    plt.title(f'Comparación de la Distribución de Valores de {climate_variable_column_name} ({min(years_to_compare)}-Q1 a {max(years_to_compare)}-Q4)')
    plt.xlabel('Año-Trimestre')
    plt.ylabel(f'Valores de {climate_variable_column_name}')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45, ha='right') # Rotate labels for better readability
    plt.tight_layout()
    plt.show()





def plot_all_climate_variables_time_series(df_input, title_suffix="Evolución a lo largo del tiempo", columns_to_plot=[]):
    """
    Generates a line plot comparing the mean trends of climate variables on a single canvas,
    each with its own y-axis scale, and adds background bars showing the total number of
    hotspots (where each row in df_input represents one hotspot).
    """
    if df_input.empty:
        print("Input DataFrame is empty. Cannot generate plots for climate variables.")
        return

    selected_climate_variable_cols = [
        'temperature_2m_mean_(C)',
        '%humedad_relativa',
        'precipitation_mean_(mm/d)',
        'elevation_m',
        'NDVI_mean',
        'NDMI_mean'
    ]

    if columns_to_plot:
        selected_climate_variable_cols = columns_to_plot

    print("Plotting trends and hotspot frequencies...")

    # 1. Configuración del Lienzo
    fig, ax_base = plt.subplots(figsize=(16, 7.5))

    lines_all = []
    labels_all = []
    colors = sns.color_palette("muted", len(selected_climate_variable_cols))
    x_ticks_labels = None

    # --- CONTAR REGISTROS (CADA FILA ES UN HOTSPOT) ---
    # Asegurar que existan las columnas de tiempo en el DataFrame copia
    df_working = df_input.copy()
    if 'Year' not in df_working.columns or 'Quarter' not in df_working.columns:
        df_working['acq_date'] = pd.to_datetime(df_working['acq_date'])
        df_working['Year'] = df_working['acq_date'].dt.year
        df_working['Quarter'] = df_working['acq_date'].dt.quarter

    # .size() cuenta el total de filas (hotspots) por grupo
    df_hotspots = df_working.groupby(['Year', 'Quarter']).size().reset_index(name='hotspot_count')
    df_hotspots['YearQuarter'] = df_hotspots['Year'].astype(str) + '-Q' + df_hotspots['Quarter'].astype(str)
    df_hotspots = df_hotspots.sort_values(by=['Year', 'Quarter']).reset_index(drop=True)

    x_ticks_labels = df_hotspots['YearQuarter'].tolist()

    # Dibujar las barras grises de fondo (Frecuencia de Hotspots)
    bars = ax_base.bar(
        df_hotspots['YearQuarter'],
        df_hotspots['hotspot_count'],
        color='#95a5a6',
        alpha=0.44, # Sutil para que no opaque las líneas climáticas
        width=0.6,
        label='Cantidad de Hotspots'
    )

    # Estilo del eje Y izquierdo (Hotspots)
    ax_base.set_ylabel('Cantidad de Hotspots (Registros)', color='#7f8c8d', fontweight='bold', fontsize=10)
    ax_base.tick_params(axis='y', labelcolor='#7f8c8d', labelsize=9)
    ax_base.spines['left'].set_edgecolor('#7f8c8d')
    ax_base.spines['left'].set_linewidth(2.0)

    # Agregar las barras a la lista de la leyenda
    lines_all.append(bars)
    labels_all.append('Frecuencia de Hotspots')
    # --------------------------------------------------

    # 2. Bucle para procesar y añadir las variables climáticas
    for i, col_name in enumerate(selected_climate_variable_cols):
        # Todos los ejes climáticos se vuelven gemelos y se escalonan a la derecha
        ax = ax_base.twinx()

        offset = i * 75
        ax.spines['right'].set_position(('outward', offset))
        ax.spines['right'].set_visible(True)

        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

        # Tu función externa para promediar las variables climáticas
        df_summary_var = analyze_climate_by_quarter(df_input, climate_variable_column_name=col_name)

        if df_summary_var.empty:
            print(f"Warning: No data for {col_name}, skipping.")
            line_placeholder, = ax.plot([], [], color=colors[i], linestyle='--', label=f'{col_name} (Sin Datos)')
            lines_all.append(line_placeholder)
            labels_all.append(line_placeholder.get_label())
            continue

        df_plot = df_summary_var.copy()
        df_plot['YearQuarter'] = df_plot['Year'].astype(str) + '-Q' + df_plot['Quarter'].astype(str)
        df_plot = df_plot.sort_values(by=['Year', 'Quarter']).reset_index(drop=True)

        df_plot['Std_Dev'] = df_plot['Values_List'].apply(lambda x: np.std(x) if len(x) > 1 else np.nan)

        # Graficar líneas de tendencia climática
        line, = ax.plot(
            df_plot['YearQuarter'],
            df_plot['Mean_Value'],
            color=colors[i],
            marker='o',
            markersize=6,
            linewidth=2,
            markeredgecolor='w',
            label=col_name.replace('_', ' ').title()
        )
        lines_all.append(line)
        labels_all.append(line.get_label())

        # Desviación estándar (Sombreado)
        if not df_plot['Std_Dev'].isnull().all():
            ax.fill_between(
                df_plot['YearQuarter'],
                df_plot['Mean_Value'] - df_plot['Std_Dev'],
                df_plot['Mean_Value'] + df_plot['Std_Dev'],
                color=colors[i],
                alpha=0.06
            )

        # Formatear el eje Y de la derecha actual
        clean_label = col_name.split('(')[0].replace('_', ' ').strip().title()
        ax.set_ylabel(clean_label, color=colors[i], fontweight='bold', fontsize=10)
        ax.tick_params(axis='y', labelcolor=colors[i], labelsize=9)

        ax.spines['right'].set_edgecolor(colors[i])
        ax.spines['right'].set_linewidth(2.0)

    # 3. Ajustes finales del Eje X (Común para todo el gráfico)
    ax_base.spines['top'].set_visible(False)
    ax_base.set_xlabel('Año - Trimestre', fontweight='bold', fontsize=11, labelpad=10)

    if x_ticks_labels:
        ax_base.set_xticks(range(len(x_ticks_labels)))
        ax_base.set_xticklabels(x_ticks_labels, rotation=45, ha='right', fontsize=9)

    # Cuadrícula de fondo solo horizontal para las barras de conteo
    ax_base.grid(True, axis='y', linestyle=':', alpha=0.4, color='#999999')

    # 4. Título y Leyenda inferior unificada
    plt.title(f'Evolución Climática vs Densidad de Hotspots\n{title_suffix}', fontsize=14, fontweight='bold', pad=20)

    fig.legend(
        lines_all,
        labels_all,
        loc='upper center',
        bbox_to_anchor=(0.5, -0.05),
        ncol=3,
        frameon=True,
        facecolor='white',
        edgecolor='#e0e0e0'
    )

    plt.tight_layout()
    # Distribución de márgenes (Izquierda para barras, Derecha para los 4 ejes climáticos flotantes)
    plt.subplots_adjust(bottom=0.20, left=0.08, right=0.76)

    plt.show()