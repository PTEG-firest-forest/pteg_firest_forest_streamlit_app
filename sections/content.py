import streamlit as st

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

        # Mostrar el mapa usando Streamlit
        st.map(gdf_resultado)
