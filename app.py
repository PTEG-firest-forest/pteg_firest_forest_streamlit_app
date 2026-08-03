import streamlit as st

from classes.mongo_connector import mongo_connector
from sections.content import render_content, render_hexagonal_map
from sections.sidebar import render_sidebar
from utils.load_data import load_data_from_mongo
from utils.map_functions import crear_rejilla_hexagonal_4326, load_roi

# Configuración de la página
st.set_page_config(
    page_title="Monitoreo de Focos de Calor", page_icon="🔥", layout="wide"
)


# Inicializar la conexión usando caché de recurso para que persista entre ejecuciones
@st.cache_resource
def init_connection():
    return mongo_connector()


db = init_connection()

# --- BARRA LATERAL DE FILTROS ---
selected_year, selected_quarter = render_sidebar(db)

# --- CARGA Y PROCESAMIENTO DE DATOS ---
with st.spinner("Cargando datos desde MongoDB..."):
    df_data = load_data_from_mongo(_db=db, year=selected_year, quarter=selected_quarter)


# --- PANEL PRINCIPAL ---
render_content(df_data, selected_year, selected_quarter)

# Renderizar el mapa con la rejilla hexagonal y los datos de focos de calor
render_hexagonal_map(df_data)
