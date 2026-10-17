"""
Módulo de procesamiento espacial.
Se encarga de generar coordenadas aleatorias y buscar enriquecimiento 
sociodemográfico realizando cruces espaciales y tabulares.
"""

import os
import random
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


def cargar_y_cruzar_datos(ruta_mapa, ruta_master):
    """
    Carga un archivo geográfico y uno maestro, y realiza un inner join.
    """
    gdf_mapa = gpd.read_parquet(ruta_mapa)
    df_master = pd.read_parquet(ruta_master)
    return gdf_mapa.merge(df_master, on="manz_ccnct", how="inner")


def generar_coordenada_aleatoria_colombia(gdf):
    """
    Genera latitud y longitud garantizando que cae dentro de un polígono válido 
    de forma ultra rápida (Milisegundos).
    """
    manzana_aleatoria = gdf.sample(1).iloc[0]
    geometria_manzana = manzana_aleatoria.geometry

    min_lon, min_lat, max_lon, max_lat = geometria_manzana.bounds

    while True:
        lon_candidata = random.uniform(min_lon, max_lon)
        lat_candidata = random.uniform(min_lat, max_lat)
        punto_candidato = Point(lon_candidata, lat_candidata)

        if geometria_manzana.contains(punto_candidato):
            return lat_candidata, lon_candidata


def buscar_manzana_por_coordenada(gdf, lat, lon):
    """
    Retorna el GeoDataFrame filtrado con la manzana que contiene el punto.
    """
    punto_busqueda = Point(lon, lat)
    return gdf[gdf.geometry.contains(punto_busqueda)]


def identificar_municipio_por_coordenada(gdf_nacional, lat, lon):
    """
    Busca la coordenada en el mapa nacional y extrae los primeros 5 dígitos 
    del código de manzana, los cuales corresponden al código Divipola.
    """
    punto = Point(lon, lat)
    resultado = gdf_nacional[gdf_nacional.geometry.contains(punto)]

    if not resultado.empty:
        codigo_manzana = str(resultado.iloc[0]['manz_ccnct'])
        return codigo_manzana[:5]
    return None


def buscar_y_enriquecer_coordenada_dinamica(lat, lon, gdf_nacional,
                                            ruta_segmentados, ruta_master):
    """
    Orquesta el flujo:
    1. Identifica el municipio.
    2. Carga el parquet de ese municipio (solo área y geometría).
    3. Lee el maestro (solo las variables requeridas por negocio).
    4. Cruza los datos y devuelve la manzana específica.
    """
    codigo_mun = identificar_municipio_por_coordenada(gdf_nacional, lat, lon)

    if not codigo_mun:
        return None

    ruta_parquet_municipio = os.path.join(ruta_segmentados, f"manzanas_{codigo_mun}.parquet")

    if not os.path.exists(ruta_parquet_municipio):
        return None

    # 1. Definir columnas exactas para el MAPA
    columnas_mapa = [
        "manz_ccnct",  # Llave primaria obligatoria
        "manz_narea",  # El área que solicitaste
        "geometry"     # Obligatorio para poder hacer la búsqueda espacial (contains)
    ]

    # 2. Definir columnas exactas para el MAESTRO
    columnas_maestro = [
        "manz_ccnct",  # Llave primaria obligatoria
        "cnue_total_ue", 
        "cnue_n_drogueria", 
        "cnue_n_panaderia", 
        "cnue_n_restaurante", 
        "cnue_n_super_tiendas", 
        "cnue_n_carnicos", 
        "ovt_dist_min_m", 
        "ovt_n_poi_300m", 
        "via_dist_secundaria_m", 
        "gtfs_dist_parada_m", 
        "gtfs_disponible", 
        "cnpv_pct_estrato_bajo"
    ]

    # 3. Carga partición y maestro filtrando desde el disco
    # Usamos columns=... en AMBOS para no cargar nada extra a la RAM
    gdf_municipio = gpd.read_parquet(ruta_parquet_municipio, columns=columnas_mapa)
    df_master = pd.read_parquet(ruta_master, columns=columnas_maestro)

    # 4. Cruce de datos
    gdf_cruzado = gdf_municipio.merge(df_master, on="manz_ccnct", how="inner")

    # 5. Retornar la búsqueda filtrada
    return buscar_manzana_por_coordenada(gdf_cruzado, lat, lon)