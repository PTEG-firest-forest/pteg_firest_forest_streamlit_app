import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import MultiPolygon, Point, Polygon


def crear_rejilla_hexagonal_4326(gdf_roi, radio_km):
    """
    Toma un GeoDataFrame en EPSG:4326, lo proyecta a un sistema métrico local,
    genera los hexágonos de 'radio_km' y los devuelve en EPSG:4326.
    """
    # 1. Proyectar a un sistema métrico local automáticamente (UTM ideal para la zona)
    # estimate_utm_crs es excelente porque encuentra la zona UTM perfecta para tu ROI
    crs_metrico = gdf_roi.estimate_utm_crs()
    roi_proyectada = gdf_roi.to_crs(crs_metrico)

    # Combinar en una sola geometría si el ROI tiene múltiples filas/polígonos
    poligono_union = roi_proyectada.union_all()

    # 2. Definir parámetros del hexágono en metros
    radio = radio_km * 1000  # Convertir a metros
    ancho_hex = radio * np.sqrt(3)
    alto_hex = radio * 2

    # Límites del polígono en metros
    minx, miny, maxx, maxy = poligono_union.bounds

    # Vectores de movimiento
    x_coords = np.arange(minx - ancho_hex, maxx + ancho_hex, ancho_hex)
    y_coords = np.arange(miny - alto_hex, maxy + alto_hex, alto_hex * 0.75)

    hexagonos_lista = []

    # 3. Generar la rejilla
    for i, y in enumerate(y_coords):
        x_offset = (ancho_hex / 2) if i % 2 == 1 else 0

        for x in x_coords:
            cx = x + x_offset
            cy = y

            puntos = []
            for j in range(6):
                angulo = np.deg2rad(60 * j + 30)
                px = cx + radio * np.cos(angulo)
                py = cy + radio * np.sin(angulo)
                puntos.append((px, py))

            hex_poly = Polygon(puntos)

            # Validar si el hexágono intersecta la región de interés
            if hex_poly.intersects(poligono_union):
                hexagonos_lista.append(hex_poly)

    # 4. Crear el GeoDataFrame en el CRS métrico
    gdf_hex_metros = gpd.GeoDataFrame(geometry=hexagonos_lista, crs=crs_metrico)

    # 5. Reproyectar de vuelta a EPSG:4326 para que sea compatible con tus mapas originales
    gdf_hex_final = gdf_hex_metros.to_crs("EPSG:4326")

    return gdf_hex_final


def procesar_datos_hexagonales(gdf_hexagonos, df_datos):
    """
    Procesa datos de hexágonos y puntos para generar un resumen por hexágono.

    Parameters:
    -----------
    gdf_hexagonos : geopandas.GeoDataFrame
        GeoDataFrame con los hexágonos de la región de interés
        Debe tener columna 'geometry' con los polígonos
    df_datos : pandas.DataFrame
        DataFrame con los datos de los puntos (hotspots y variables ambientales)

    Returns:
    --------
    pandas.DataFrame
        DataFrame con el resumen por hexágono
    """

    # Crear copias para no modificar los originales
    gdf_hex = gdf_hexagonos.copy()
    df_datos = df_datos.copy()

    # Asegurar que el CRS sea compatible
    if gdf_hex.crs is None:
        # Si no tiene CRS, asumir WGS84 (EPSG:4326)
        gdf_hex = gdf_hex.set_crs("EPSG:4326", allow_override=True)

    # Ensure acq_date is datetime type
    df_datos["acq_date"] = pd.to_datetime(df_datos["acq_date"], errors="coerce")

    # Convertir puntos a geometría con el mismo CRS que los hexágonos
    gdf_puntos = gpd.GeoDataFrame(
        df_datos,
        geometry=gpd.points_from_xy(df_datos.longitude, df_datos.latitude),
        crs=gdf_hex.crs,
    )

    # Realizar join espacial para asignar cada punto a su hexágono
    gdf_puntos_con_hex = gpd.sjoin(
        gdf_puntos,
        gdf_hex[["geometry"]],  # Solo necesitamos la geometría para el join
        how="left",
        predicate="within",
    )

    # Agrupar por índice del hexágono (index_right es el índice del hexágono que contiene al punto)
    grouped = gdf_puntos_con_hex.groupby("index_right")

    # Calcular estadísticas agregadas, incluyendo longitude, latitude y acq_date
    df_agregado = grouped.agg(
        {
            "temperature_2m_mean_(C)": "mean",
            "%humedad_relativa": "mean",
            "precipitation_mean_(mm/d)": "mean",
            "NDVI_mean": "mean",
            "NDMI_mean": "mean",
            "land_cover_class": lambda x: (
                x.mode().iloc[0] if not x.mode().empty else None
            ),
            "longitude": "mean",  # Mean longitude of hotspots in the hexagon
            "latitude": "mean",  # Mean latitude of hotspots in the hexagon
            "acq_date": "min",  # Earliest acquisition date of hotspots in the hexagon
            "index": "count",  # Count points (hotspots)
        }
    ).reset_index()

    # Renombrar columnas
    df_agregado.columns = [
        "index",
        "temperature",
        "humidity",
        "precipitation",
        "ndvi",
        "ndmi",
        "land_cover",
        "hotspot_mean_longitude",
        "hotspot_mean_latitude",
        "hotspot_earliest_acq_date",
        "number_hotspots",
    ]

    # Asegurar que todos los hexágonos estén representados
    # Crear DataFrame con todos los índices de hexágonos
    df_completo = pd.DataFrame({"index": gdf_hex.index})
    df_resultado = df_completo.merge(df_agregado, on="index", how="left")

    # Rellenar valores nulos para hexágonos sin datos
    df_resultado["number_hotspots"] = (
        df_resultado["number_hotspots"].fillna(0).astype(int)
    )

    # Para las demás columnas, mantener NaN para hexágonos sin datos
    # o podrías rellenar con 0 si prefieres
    # df_resultado = df_resultado.fillna(0)

    return df_resultado


def procesar_datos_hexagonales_con_geometria(gdf_hexagonos, df_datos):
    """
    Versión que también mantiene la geometría de los hexágonos en el resultado.
    """

    # Obtener el DataFrame resumen
    df_resultado = procesar_datos_hexagonales(gdf_hexagonos, df_datos)

    # Unir con la geometría de los hexágonos
    gdf_resultado = gdf_hexagonos[["geometry"]].copy()
    gdf_resultado = gdf_resultado.merge(df_resultado, left_index=True, right_on="index")

    return gdf_resultado
