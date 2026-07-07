import streamlit as st

def render_sidebar(db):
    """
    Renderiza la barra lateral con los filtros de búsqueda.
    
    Args:
        db: La instancia de la conexión a MongoDB.
        
    Returns:
        tuple: (selected_year, selected_quarter)
    """
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

    return selected_year, selected_quarter
