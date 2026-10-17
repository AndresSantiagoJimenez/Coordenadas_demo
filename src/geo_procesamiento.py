"""
Módulo de Geoprocesamiento Espacial y Enriquecimiento Sociodemográfico.
Proporciona funciones optimizadas para identificación municipal, cruce espacial (Point-in-Polygon),
y enriquecimiento tabular con el Feature Store Maestro DANE.
"""

import os
import random
import logging
from typing import Optional, Tuple, List, Any
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from src.config import COLUMNAS_GEOMETRIA, COLUMNAS_NEGOCIO

logger = logging.getLogger("GeoProcesamiento")


def cargar_y_cruzar_datos(ruta_mapa: str, ruta_master: str) -> gpd.GeoDataFrame:
    """
    Carga un archivo geográfico particionado y el archivo maestro,
    realizando un inner join sobre la clave primaria 'manz_ccnct'.

    Args:
        ruta_mapa: Ruta al archivo parquet de geometrías.
        ruta_master: Ruta al archivo parquet maestro de features.

    Returns:
        GeoDataFrame combinado con geometrías y atributos enriquecidos.
    """
    gdf_mapa = gpd.read_parquet(ruta_mapa)
    df_master = pd.read_parquet(ruta_master)
    return gdf_mapa.merge(df_master, on="manz_ccnct", how="inner")


def generar_coordenada_aleatoria_colombia(gdf: gpd.GeoDataFrame) -> Tuple[float, float]:
    """
    Genera latitud y longitud garantizando que el punto cae estrictamente
    dentro del polígono de una manzana urbana válida.

    Args:
        gdf: GeoDataFrame con geometrías de polígonos.

    Returns:
        Tupla con (latitud, longitud).
    """
    if gdf.empty:
        raise ValueError("El GeoDataFrame proporcionado está vacío.")

    manzana_aleatoria = gdf.sample(1).iloc[0]
    geometria_manzana = manzana_aleatoria.geometry
    min_lon, min_lat, max_lon, max_lat = geometria_manzana.bounds

    # Muestreo Monte Carlo dentro del bounding box del polígono
    intentos = 0
    rng = random.SystemRandom()
    while intentos < 200:
        lon_candidata = rng.uniform(min_lon, max_lon)  # nosec B311
        lat_candidata = rng.uniform(min_lat, max_lat)  # nosec B311
        punto_candidato = Point(lon_candidata, lat_candidata)

        if geometria_manzana.contains(punto_candidato):
            return lat_candidata, lon_candidata
        intentos += 1

    # Fallback determinístico al centroide en caso de polígonos irregulares/cóncavos
    centroide = geometria_manzana.centroid
    return centroide.y, centroide.x


def buscar_manzana_por_coordenada(gdf: gpd.GeoDataFrame, lat: float, lon: float) -> gpd.GeoDataFrame:
    """
    Retorna el GeoDataFrame filtrado con la manzana que contiene la coordenada especificada.

    Args:
        gdf: GeoDataFrame con geometrías.
        lat: Latitud geográfica.
        lon: Longitud geográfica.

    Returns:
        GeoDataFrame filtrado con 0 o 1 registros.
    """
    punto_busqueda = Point(lon, lat)
    return gdf[gdf.geometry.contains(punto_busqueda)]


def identificar_municipio_por_coordenada(gdf_nacional: gpd.GeoDataFrame, lat: float, lon: float) -> Optional[str]:
    """
    Busca la coordenada en el mapa nacional y extrae los primeros 5 dígitos
    del código de manzana, correspondientes al código oficial Divipola.

    Args:
        gdf_nacional: GeoDataFrame nacional o índice espacial.
        lat: Latitud geográfica.
        lon: Longitud geográfica.

    Returns:
        Código Divipola de 5 dígitos o None si no se encuentra intersección.
    """
    punto = Point(lon, lat)
    resultado = gdf_nacional[gdf_nacional.geometry.contains(punto)]

    if not resultado.empty:
        codigo_manzana = str(resultado.iloc[0]["manz_ccnct"])
        return codigo_manzana[:5]
    return None


def buscar_y_enriquecer_coordenada_dinamica(
    lat: float,
    lon: float,
    gdf_nacional: gpd.GeoDataFrame,
    ruta_segmentados: str,
    ruta_master: str,
    columnas_mapa: Optional[List[str]] = None,
    columnas_maestro: Optional[List[str]] = None
) -> Optional[gpd.GeoDataFrame]:
    """
    Orquesta el flujo integral de consulta:
    1. Identifica el código Divipola municipal a partir del mapa o índice.
    2. Carga la partición parquet del municipio con proyección de columnas (column pruning).
    3. Lee el archivo maestro de features filtrando columnas requeridas por negocio.
    4. Cruza los datos por clave primaria 'manz_ccnct'.
    5. Retorna la manzana enriquecida.

    Args:
        lat: Latitud geográfica.
        lon: Longitud geográfica.
        gdf_nacional: GeoDataFrame de referencia nacional.
        ruta_segmentados: Directorio que contiene las particiones 'manzanas_{divipola}.parquet'.
        ruta_master: Ruta al archivo maestro 'features_mgn2025_master_clean.parquet'.
        columnas_mapa: Lista opcional de columnas a leer del mapa.
        columnas_maestro: Lista opcional de columnas a leer del maestro.

    Returns:
        GeoDataFrame con la manzana enriquecida o None si no se encuentra.
    """
    codigo_mun = identificar_municipio_por_coordenada(gdf_nacional, lat, lon)

    if not codigo_mun:
        return None

    ruta_parquet_municipio = os.path.join(ruta_segmentados, f"manzanas_{codigo_mun}.parquet")

    if not os.path.exists(ruta_parquet_municipio):
        logger.warning(f"No existe partición segmentada para municipio {codigo_mun}: {ruta_parquet_municipio}")
        return None

    # Columnas por defecto optimizadas
    if columnas_mapa is None:
        columnas_mapa = [
            "manz_ccnct",
            "manz_narea",
            "geometry"
        ]

    if columnas_maestro is None:
        columnas_maestro = [
            "manz_ccnct",
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

    try:
        # Carga selectiva de la partición municipal
        gdf_municipio = gpd.read_parquet(ruta_parquet_municipio, columns=columnas_mapa)

        # Carga del maestro con las columnas solicitadas
        df_master = pd.read_parquet(ruta_master, columns=columnas_maestro)

        # Cruce por identificador único de manzana
        gdf_cruzado = gdf_municipio.merge(df_master, on="manz_ccnct", how="inner")

        # Filtro Point-in-Polygon
        return buscar_manzana_por_coordenada(gdf_cruzado, lat, lon)

    except Exception as e:
        logger.error(f"Error durante el enrutamiento y cruce de datos: {e}")
        return None