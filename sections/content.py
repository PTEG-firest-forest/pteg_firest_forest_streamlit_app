import pandas as pd
import pydeck as pdk
import streamlit as st

from data.name_mappings import climate_vars_name_mapping, spectral_index_name_mapping
from utils.map_functions import (
    crear_rejilla_hexagonal_4326,
    load_roi,
    procesar_datos_hexagonales_con_geometria,
)


def render_content(df_data, selected_year, selected_quarter):
    """
    Renderiza el contenido principal de la aplicación.

    Args:
        df_data: DataFrame con los datos filtrados.
        selected_year: El año seleccionado.
        selected_quarter: El trimestre seleccionado.
    """
    # Título de la aplicación
    st.title("🔥 Panel de Control Ambiental - Datos MongoDB")
    st.markdown("Visualización y filtrado de datos meteorológicos y focos de calor.")

    # --- PANEL PRINCIPAL ---
    if not df_data.empty:
        # Métricas clave rápidas
        total_registros = len(df_data)
        avg_frp = df_data["frp"].mean() if "frp" in df_data.columns else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Registros en Periodo", f"{total_registros}")
        col2.metric("Promedio FRP (Potencia de Fuego)", f"{avg_frp:.2f}")
        col3.metric(
            "Año / Trimestre Seleccionado", f"{selected_year} - Q{selected_quarter}"
        )

        st.write("---")

        # Vista de Datos
        st.subheader("📋 Vista de Datos Filtrados")

        # Permitir al usuario expandir las columnas complejas (cv, si) si lo desea,
        # o mostrar el dataframe general
        columns_to_show = [
            "_id",
            "acq_date",
            "latitude",
            "longitude",
            "frp",
            "confidence",
            "fire_type",
            "instrument",
        ]
        existing_columns = [col for col in columns_to_show if col in df_data.columns]

        st.dataframe(df_data[existing_columns], width="stretch")

        # Mostrar un ejemplo del primer registro anidado (cv/si) de forma limpia
        with st.expander(
            "🔍 Ver detalle de variables climáticas anidadas (Primer Registro)"
        ):
            if (
                "climate_vars" in df_data.columns
                and not df_data["climate_vars"].isna().all()
            ):
                st.json(df_data["climate_vars"].iloc[0])

    else:
        st.warning(
            f"No se encontraron datos para el año {selected_year} en el Trimestre {selected_quarter}."
        )


def render_hexagonal_map(df_data=None):
    """
    Renderiza un mapa con una rejilla hexagonal y los datos de focos de calor.

    Args:
        df_data: DataFrame con los datos filtrados.
    """
    st.subheader("🗺️ Mapa de Rejilla Hexagonal")

    # filtro de ventana de tiempo para el mapa
    time_window = st.selectbox(
        "Selecciona la ventana de tiempo para el mapa:",
        options=["7 días antes", "dia de la deteccion", "7 días despues"],
        index=1,
    )

    # Mapeo de la ventana elegida a la clave interna del diccionario ('b' = before, 'o' = on-day, 'a' = after)
    key_mapping = {
        "7 días antes": (
            "b",
            "Mostrando datos de focos de calor 7 días antes de la fecha de adquisición.",
        ),
        "dia de la deteccion": (
            "o",
            "Mostrando datos de focos de calor del día de la detección.",
        ),
        "7 días despues": (
            "a",
            "Mostrando datos de focos de calor 7 días después de la fecha de adquisición.",
        ),
    }

    target_key, info_message = key_mapping[time_window]
    st.info(info_message)

    def extract_nested_dict(series, key):
        """Extrae la subclave (b, o, a) de cada fila y la convierte en un DataFrame."""
        extracted = series.apply(
            lambda x: x.get(key, {}) if isinstance(x, dict) else {}
        )
        return pd.json_normalize(extracted)

    # Extraer y renombrar las variables climáticas e índices espectrales
    climate_vars_df = extract_nested_dict(df_data["climate_vars"], target_key).rename(
        columns=climate_vars_name_mapping
    )
    spectral_indices_df = extract_nested_dict(
        df_data["spectral_index"], target_key
    ).rename(columns=spectral_index_name_mapping)

    # Asegurar que los índices coincidan antes del concat
    climate_vars_df.index = df_data.index
    spectral_indices_df.index = df_data.index

    # Unir todo eliminando las columnas anidadas originales
    df_data = pd.concat(
        [
            df_data.drop(columns=["climate_vars", "spectral_index"]),
            climate_vars_df,
            spectral_indices_df,
        ],
        axis=1,
    )

    # Debug
    st.dataframe(df_data, width="stretch")

    # carga de roi
    gdf_roi = load_roi("data/cordillera_central_prescisa_roi.csv")

    # Crear la rejilla hexagonal
    gdf_hex = crear_rejilla_hexagonal_4326(_gdf_roi=gdf_roi, radio_km=1.0)

    if df_data is None or df_data.empty:
        st.warning("No hay datos para mostrar en el mapa.")
        st.map(gdf_hex)
        return
    else:
        # Procesar los datos para agregarlos a la rejilla
        gdf_resultado = procesar_datos_hexagonales_con_geometria(
            _gdf_hexagonos=gdf_hex, df_datos=df_data
        )
        st.dataframe(gdf_resultado, width="stretch")
        # Mostrar el mapa usando Streamlit
        
        # Eliminamos filas con latitud o longitud nula para evitar errores en st.map()
        gdf_resultado_map = gdf_resultado.dropna(subset=["latitude", "longitude"])

        # 2. Convertir la geometría a GeoJSON para PyDeck
        geojson_data = gdf_resultado_map.__geo_interface__

        # 3. Definir la capa del mapa
        layer = pdk.Layer(
            "GeoJsonLayer",
            geojson_data,
            opacity=0.4,
            stroked=True,
            filled=True,
            get_fill_color="[255, 69, 0, 160]",
            get_line_color="[255, 255, 255, 200]",
            get_line_width=2,
            pickable=True,
        )

        # 4. Configurar la vista centrada en los datos
        view_state = pdk.ViewState(
            latitude=gdf_resultado_map["latitude"].mean(),
            longitude=gdf_resultado_map["longitude"].mean(),
            zoom=8,
        )

        # 5. Renderizar el mapa
        st.pydeck_chart(
            pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={"text": "Focos: {number_hotspots}\nTemp: {temperature}°C"}
            )
        )
