
# ==================================================================================================================
# ==================================================================================================================
# mapeo de nombres de columnas de los datasets de hotspots, climate_vars y spectral_index
# ==================================================================================================================
# ==================================================================================================================

hotspots_data_name_mapping = {
    "idx": "index",
    "bt4": "bright_ti4",
    "bt5": "bright_ti5",
    "conf": "confidence",
    "cv": "climate_vars",
    "date": "acq_date",
    "dn": "daynight",
    "f_type": "fire_type",
    "frp": "frp",
    "inst": "instrument",
    "lat": "latitude",
    "lc_class": "land_cover_class",
    "lc_code": "land_cover_code",
    "lon": "longitude",
    "sat": "satellite",
    "scan": "scan",
    "si": "spectral_index",
    "time": "acq_time",
    "track": "track",
    "type": "type",
    "ver": "version",
}

climate_vars_name_mapping = {
    "t_avg": "temperature_2m_mean_(C)",
    "t_min": "temperature_2m_min_(C)",
    "t_max": "temperature_2m_max_(C)",
    "dp_avg": "dewpoint_2m_mean_(C)",
    "dp_min": "dewpoint_2m_min_(C)",
    "dp_max": "dewpoint_2m_max_(C)",
    "prec": "precipitation_mean_(mm/d)",
    "rh": "%humedad_relativa",
    "ws": "wind_speed_mean_(m/s)",
    "wd": "wind_direction_deg",
    "el": "elevation_m",
}


spectral_index_name_mapping = {
    "v_max": "NDVI_max",
    "v_avg": "NDVI_mean",
    "v_min": "NDVI_min",
    "m_max": "NDMI_max",
    "m_avg": "NDMI_mean",
    "m_min": "NDMI_min",
}
