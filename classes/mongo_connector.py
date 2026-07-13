import os
import streamlit as st
import pandas as pd
from pymongo import MongoClient
from data.name_mappings import hotspots_data_name_mapping, climate_vars_name_mapping, spectral_index_name_mapping

# **************************************************************
# MongoDB Connector Class
# **************************************************************

class mongo_connector:
    def __init__(self, uri: str = None, db_name: str = None, collection_name: str = None):
        # Intentar leer de st.secrets (Streamlit) o variables de entorno, con fallbacks
        self.uri = uri or st.secrets.get("MONGO_URI", os.getenv("MONGO_URI", "mongodb://localhost:27017"))
        self.db_name = db_name or st.secrets.get("MONGO_DB", os.getenv("MONGO_DB", "environmental_db"))
        self.collection_name = collection_name or st.secrets.get("MONGO_COLLECTION", os.getenv("MONGO_COLLECTION", "hotspots"))
        self.client = None
        self.db = None
        self.collection = None
        
        self.connect()

    def connect(self):
        """Establece la conexión con la base de datos."""
        try:
            self.client = MongoClient(self.uri)
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
        except Exception as e:
            st.error(f"Error al conectar a MongoDB: {e}")

    def get_available_years(self):
        """Obtiene la lista única de años disponibles en la colección basándose en el campo 'date'."""
        pipeline = [
            {
                "$group": {
                    "_id": {"$year": "$date"}
                }
            },
            {"$sort": {"_id": -1}}
        ]
        try:
            result = list(self.collection.aggregate(pipeline))
            years = [doc["_id"] for doc in result if doc["_id"] is not None]
            return years if years else [2014] # Año por defecto basado en tu muestra si está vacío
        except Exception as e:
            st.error(f"Error al obtener años: {e}")
            return [2014]

    def get_filtered_data(self, year: int, quarter: int) -> pd.DataFrame:
        """
        Filtra los datos por año y trimestre utilizando agregaciones de MongoDB.
        """
        pipeline = [
            {
                "$project": {
                    "year": {"$year": "$date"},
                    "quarter": {"$ceil": {"$divide": [{"$month": "$date"}, 3]}},
                    # Traemos los campos planos y anidados necesarios
                    "date": 1,
                    "lat": 1,
                    "lon": 1,
                    "frp": 1,
                    "conf": 1,
                    "f_type": 1,
                    "inst": 1,
                    "bt4": 1,
                    "cv": 1,
                    "si": 1
                }
            },
            {
                "$match": {
                    "year": year,
                    "quarter": quarter
                }
            }
        ]
        
        try:
            cursor = self.collection.aggregate(pipeline)
            df = pd.DataFrame(list(cursor))
            df.rename(columns=hotspots_data_name_mapping, inplace=True)
            if not df.empty:
                # Limpiar la columna _id de BSON a string para evitar problemas de serialización en Streamlit
                df["_id"] = df["_id"].astype(str)
            return df
        except Exception as e:
            st.error(f"Error al filtrar datos: {e}")
            return pd.DataFrame()