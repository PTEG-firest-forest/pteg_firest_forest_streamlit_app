import streamlit as st
from classes.mongo_connector import mongo_connector

# Configuración de la página
st.set_page_config(
    page_title="Monitoreo de Focos de Calor",
    page_icon="🔥",
    layout="wide"
)

# Inicializar la conexión usando caché de recurso para que persista entre ejecuciones
@st.cache_resource
def init_connection():
    return mongo_connector()

db = init_connection()

# Título de la aplicación
st.title("🔥 Panel de Control Ambiental - Datos MongoDB")
st.markdown("Visualización y filtrado de datos meteorológicos y focos de calor.")

# --- BARRA LATERAL DE FILTROS ---
st.sidebar.header("Filtros de Búsqueda")

# Obtener años dinámicamente desde MongoDB
available_years = db.get_available_years()
selected_year = st.sidebar.selectbox("Selecciona el Año", options=available_years, index=0)

# Selector de trimestre
quarters = {
    "Trimestre 1 (Ene - Mar)": 1,
    "Trimestre 2 (Abr - Jun)": 2,
    "Trimestre 3 (Jul - Sep)": 3,
    "Trimestre 4 (Oct - Dic)": 4
}
selected_quarter_label = st.sidebar.selectbox("Selecciona el Trimestre", options=list(quarters.keys()))
selected_quarter = quarters[selected_quarter_label]

# --- CARGA Y PROCESAMIENTO DE DATOS ---
with st.spinner("Cargando datos desde MongoDB..."):
    df_data = db.get_filtered_data(selected_year, selected_quarter)

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