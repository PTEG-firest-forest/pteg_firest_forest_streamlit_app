import streamlit as st


@st.cache_data(ttl=3600, show_spinner="Cargando datos de MongoDB...")
def load_data_from_mongo(_db, year, quarter):
    """
    Carga y filtra los datos desde MongoDB según el año y trimestre seleccionados.

    Args:
        _db: Instancia de la clase mongo_connector.
        year: Año seleccionado.
        quarter: Trimestre seleccionado.

    Returns:
        DataFrame con los datos filtrados.
    """
    df_data = _db.get_filtered_data(year, quarter)
    return df_data
