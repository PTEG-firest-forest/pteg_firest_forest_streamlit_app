import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import joblib  # Para cargar tu modelo predictivo

# 1. Configuración de la página (Debe ser la primera línea de Streamlit)
st.set_page_config(
    page_title="Dashboard de Hotspots e Incendios",
    page_icon="🔥",
    layout="wide"
)

# 2. Carga optimizada de datos
@st.cache_data
def load_data():
    # Reemplaza con la ruta de tus datos. 
    # Asegúrate de parsear las fechas para los lineplots temporales.
    df = pd.read_csv("data/VIIRS_SUOMI_clima_2020.csv", parse_dates=['acq_date'])
    return df

df = load_data()

# 3. Barra lateral para filtros globales
st.sidebar.header("Filtros de Análisis")
# Ejemplo: Filtro por año o rango de fechas
años = df['acq_date'].dt.year.unique()
año_seleccionado = st.sidebar.multiselect("Selecciona el Año", options=años, default=años)

# Filtrar el dataframe basado en la selección
df_filtrado = df[df['acq_date'].dt.year.isin(año_seleccionado)]

# 4. Título Principal
st.title("🔥 Monitoreo y Predicción de Hotspots")
st.markdown("Análisis longitudinal de dinámicas de incendios y modelado predictivo.")

# --- SECCIÓN 1: MÉTRICAS CLAVE ---
metrica1, metrica2 = st.columns(2)
metrica1.metric("Total de Hotspots en Selección", len(df_filtrado))
metrica2.metric("Promedio de Confianza/Frp", f"{df_filtrado['frp'].mean():.2f}")

# --- SECCIÓN 2: GRÁFICOS (Lineplots & Boxplots) ---
st.header("📊 Análisis Estadístico y Temporal")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Tendencia Temporal (Lineplot)")
    # Agrupar por mes/año según tus datos
    df_temporal = df_filtrado.groupby(df_filtrado['acq_date'].dt.to_period('M')).size().reset_index(name='conteo')
    df_temporal['acq_date'] = df_temporal['acq_date'].dt.to_timestamp()
    
    fig_line = px.line(df_temporal, x='acq_date', y='conteo', title="Evolución de Hotspots en el Tiempo")
    st.plotly_chart(fig_line, width='stretch')

with col2:
    st.subheader("Distribución de Atributos (Boxplot)")
    # Ejemplo con FRP o Confianza
    fig_box = px.box(df_filtrado, y='frp', title="Distribución de la Potencia Radiativa del Fuego (FRP)")
    st.plotly_chart(fig_box, width='stretch')

# --- SECCIÓN 3: MAPAS ---
st.header("🗺️ Visualización Geoespacial")
st.markdown("Distribución geográfica de los puntos críticos detectados.")

# Mapa de densidad interactivo nativo de Plotly (muy eficiente para miles de puntos)
fig_map = px.density_map(
    df_filtrado, 
    lat='latitude', 
    lon='longitude', 
    z='frp', 
    radius=10,
    center=dict(lat=df_filtrado['latitude'].mean(), lon=df_filtrado['longitude'].mean()), 
    zoom=5,
    map_style="open-street-map"  # O "carto-positron"
)
st.plotly_chart(fig_map, width='stretch')

# --- SECCIÓN 4: PREDICCIÓN ---
st.header("🤖 Módulo de Predicción")
st.markdown("Introduce las variables hidrometeorológicas o temporales para estimar el riesgo.")

# Aquí creas los inputs que necesita tu algoritmo (ej: Temperatura, NDVI, Mes)
col_in1, col_in2 = st.columns(2)
with col_in1:
    input_temp = st.number_input("Temperatura de la Superficie (°C)", value=25.0)
with col_in2:
    input_ndvi = st.slider("Índice NDVI", min_value=-1.0, max_value=1.0, value=0.4)

if st.button("Calcular Riesgo de Hotspot"):
    # Cargar el modelo guardado
    # modelo = joblib.load("models/modelo_predictivo.pkl")
    # prediccion = modelo.predict([[input_temp, input_ndvi]])
    
    # Simulación de respuesta para el esqueleto
    prediccion_dummy = "Alto Riesgo" if input_temp > 35 and input_ndvi < 0.2 else "Bajo Riesgo"
    
    if prediccion_dummy == "Alto Riesgo":
        st.error(f"Resultado de la Predicción: {prediccion_dummy}")
    else:
        st.success(f"Resultado de la Predicción: {prediccion_dummy}")