"""
GeoDataIQ Colombia - Enterprise Geospatial Feature Store & Spatial Data Routing Engine.
"""

from src.config import tiene_datos_completos, tiene_datos_muestra
from src.governance import DataQualityValidator, DataGovernanceCatalog, DataQualityReport
from src.engine import SpatialDataEngine, EnrichedQueryResult
from src.geo_procesamiento import (
    cargar_y_cruzar_datos,
    generar_coordenada_aleatoria_colombia,
    buscar_manzana_por_coordenada,
    identificar_municipio_por_coordenada,
    buscar_y_enriquecer_coordenada_dinamica,
)

__version__ = "1.0.0"
__all__ = [
    "SpatialDataEngine",
    "EnrichedQueryResult",
    "DataQualityValidator",
    "DataGovernanceCatalog",
    "DataQualityReport",
    "cargar_y_cruzar_datos",
    "generar_coordenada_aleatoria_colombia",
    "buscar_manzana_por_coordenada",
    "identificar_municipio_por_coordenada",
    "buscar_y_enriquecer_coordenada_dinamica",
    "tiene_datos_completos",
    "tiene_datos_muestra"
]
