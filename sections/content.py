import streamlit as st

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
        col3.metric("Año / Trimestre Seleccionado", f"{selected_year} - Q{selected_quarter}")

        st.write("---")
        
        # Vista de Datos
        st.subheader("📋 Vista de Datos Filtrados")
        
        # Permitir al usuario expandir las columnas complejas (cv, si) si lo desea, 
        # o mostrar el dataframe general
        columns_to_show = ["_id", "date", "lat", "lon", "frp", "conf", "f_type", "inst"]
        existing_columns = [col for col in columns_to_show if col in df_data.columns]
        
        st.dataframe(df_data[existing_columns], width='stretch')
        
        # Mostrar un ejemplo del primer registro anidado (cv/si) de forma limpia
        with st.expander("🔍 Ver detalle de variables climáticas anidadas (Primer Registro)"):
            if "cv" in df_data.columns and not df_data["cv"].isna().all():
                st.json(df_data["cv"].iloc[0])

    else:
        st.warning(f"No se encontraron datos para el año {selected_year} en el Trimestre {selected_quarter}.")
