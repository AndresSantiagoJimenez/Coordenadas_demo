"""
Módulo de Configuración Centralizada - GeoDataIQ.
Define rutas, constantes espaciales, columnas de negocio y gobernanza del proyecto.
"""

import os
from pathlib import Path
from typing import List, Dict, Any

# Rutas base del proyecto
BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = BASE_DIR / "Data" if (BASE_DIR / "Data").exists() else BASE_DIR / "data"

_sample_candidate = DATA_DIR / "sample"
SAMPLE_DIR: Path = _sample_candidate if _sample_candidate.exists() else BASE_DIR / "data" / "sample"

_meta_candidate = DATA_DIR / "metadata"
METADATA_DIR: Path = _meta_candidate if _meta_candidate.exists() else BASE_DIR / "data" / "metadata"

# Rutas de datos completos (Capa Gold local)
RUTA_NACIONAL_COMPLETA: Path = DATA_DIR / "DANE" / "MGN2025_URB_MANZANA" / "MGN_URB_MANZANA_CLEAN.parquet"
RUTA_SEGMENTADOS_COMPLETA: Path = DATA_DIR / "DANE" / "segmentado_clean"
RUTA_MASTER_COMPLETA: Path = DATA_DIR / "features_mgn2025" / "features_mgn2025_master_clean.parquet"

# Rutas de datos de muestra (Sample / Demostración / CI)
RUTA_MANZANAS_SAMPLE: Path = SAMPLE_DIR / "manzanas_sample.parquet"
RUTA_MASTER_SAMPLE: Path = SAMPLE_DIR / "features_master_sample.parquet"
RUTA_MUNICIPIOS_BBOX: Path = METADATA_DIR / "municipios_bbox.parquet"

# Parámetros espaciales de Colombia (EPSG:4326 - WGS84)
BBOX_COLOMBIA: Dict[str, float] = {
    "min_lat": -4.3,
    "max_lat": 13.5,
    "min_lon": -81.8,
    "max_lon": -66.8
}

CRS_WGS84: str = "EPSG:4326"
CRS_ORIGEN_NACIONAL: str = "EPSG:9377"

# Columnas optimizadas para lectura de geometrías (Memory Pruning)
COLUMNAS_GEOMETRIA: List[str] = [
    "manz_ccnct",
    "mpio_cdpmp",
    "manz_narea",
    "geometry"
]

# Columnas clave del Feature Store Maestro
COLUMNAS_NEGOCIO: List[str] = [
    "manz_ccnct",
    "mpio_cdpmp",
    "clas_ccdgo",
    "latitud",
    "longitud",
    "tvivienda",
    "viv_2025",
    "viv_delta_2018_2025",
    "viv_delta_rel_w",
    "cnue_total_ue",
    "cnue_n_super_tiendas",
    "cnue_n_panaderia",
    "cnue_n_drogueria",
    "cnue_n_licorera",
    "cnue_n_restaurante",
    "cnue_n_carnicos",
    "cnue_disponible",
    "ovt_n_poi_300m",
    "ovt_dist_min_m",
    "ovt_n_poi_300m_hi",
    "ovt_n_restbar_300m",
    "ovt_n_super_300m",
    "ovt_n_colegio_500m",
    "ovt_n_banco_500m",
    "via_dist_primaria_m",
    "via_dist_secundaria_m",
    "via_clase_max_100m",
    "via_n_conectores_50m",
    "via_n_conectores_100m",
    "via_n_conectores_300m",
    "gtfs_dist_parada_m",
    "gtfs_disponible",
    "cnpv_pct_secundaria",
    "cnpv_pct_superior",
    "cnpv_pct_sin_educ",
    "cnpv_pct_apto",
    "cnpv_pct_cuarto",
    "cnpv_pct_con_internet",
    "cnpv_pct_estrato_alto",
    "cnpv_pct_estrato_bajo",
    "cnpv_pct_uso_mixto",
    "cnpv_disponible"
]

# Diccionario de departamentos y ciudades principales para UI
DEPARTAMENTOS_COLOMBIA: Dict[str, str] = {
    "05": "Antioquia",
    "08": "Atlántico",
    "11": "Bogotá, D.C.",
    "13": "Bolívar",
    "15": "Boyacá",
    "17": "Caldas",
    "18": "Caquetá",
    "19": "Cauca",
    "20": "Cesar",
    "23": "Córdoba",
    "25": "Cundinamarca",
    "27": "Chocó",
    "41": "Huila",
    "44": "La Guajira",
    "47": "Magdalena",
    "50": "Meta",
    "52": "Nariño",
    "54": "Norte de Santander",
    "63": "Quindío",
    "66": "Risaralda",
    "68": "Santander",
    "70": "Sucre",
    "73": "Tolima",
    "76": "Valle del Cauca",
    "81": "Arauca",
    "85": "Casanare",
    "86": "Putumayo",
    "88": "San Andrés y Providencia",
    "91": "Amazonas",
    "94": "Guainía",
    "95": "Guaviare",
    "97": "Vaupés",
    "99": "Vichada"
}

CIUDADES_PREDEFINIDAS: Dict[str, Dict[str, Any]] = {
    "Bogotá (Parque de la 93)": {"lat": 4.6766, "lon": -74.0531, "divipola": "11001"},
    "Bogotá (Centro Internacional)": {"lat": 4.6158, "lon": -74.0699, "divipola": "11001"},
    "Medellín (El Poblado)": {"lat": 6.2088, "lon": -75.5684, "divipola": "05001"},
    "Medellín (Laureles)": {"lat": 6.2443, "lon": -75.5922, "divipola": "05001"},
    "Cali (Granada / Versalles)": {"lat": 3.4578, "lon": -76.5332, "divipola": "76001"},
    "Barranquilla (El Prado)": {"lat": 10.9982, "lon": -74.7958, "divipola": "08001"},
    "Cartagena (Centro Histórico)": {"lat": 10.4236, "lon": -75.5511, "divipola": "13001"},
    "Bucaramanga (Cabecera del Llano)": {"lat": 7.1189, "lon": -73.1098, "divipola": "68001"}
}


def tiene_datos_completos() -> bool:
    """Verifica si los datos completos DANE (3+ GB) están disponibles localmente."""
    return (
        RUTA_NACIONAL_COMPLETA.exists()
        and RUTA_SEGMENTADOS_COMPLETA.exists()
        and RUTA_MASTER_COMPLETA.exists()
    )


def tiene_datos_muestra() -> bool:
    """Verifica si el dataset de muestra para portafolio/demo está disponible."""
    return RUTA_MANZANAS_SAMPLE.exists() and RUTA_MASTER_SAMPLE.exists()
