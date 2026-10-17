"""
Motor de Enrutamiento y Geoprocesamiento Espacial de Alta Eficiencia (Spatial Data Engine).
Orquesta la búsqueda jerárquica (Macro Bounding Box -> Partición Municipal -> PiP -> Pushdown Master),
con métricas de latencia, caching y fallback transparente a modo muestra.
"""

import os
import time
import random
import logging
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, List

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from src.config import (
    RUTA_NACIONAL_COMPLETA,
    RUTA_SEGMENTADOS_COMPLETA,
    RUTA_MASTER_COMPLETA,
    RUTA_MANZANAS_SAMPLE,
    RUTA_MASTER_SAMPLE,
    RUTA_MUNICIPIOS_BBOX,
    COLUMNAS_GEOMETRIA,
    COLUMNAS_NEGOCIO,
    DEPARTAMENTOS_COLOMBIA,
    tiene_datos_completos,
    tiene_datos_muestra
)
from src.governance import DataQualityValidator, DataQualityReport

# Configuración de Logging Estructurado
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("GeoDataEngine")


@dataclass
class EnrichedQueryResult:
    """Resultado estructurado de consulta enriquecida de una coordenada."""
    encontrado: bool
    latitud: float
    longitud: float
    manz_ccnct: Optional[str]
    codigo_divipola: Optional[str]
    municipio_nombre: Optional[str]
    departamento_nombre: Optional[str]
    area_m2: Optional[float]
    geometria: Optional[Any]
    features: Dict[str, Any]
    calidad: Optional[DataQualityReport]
    latencia_ms: float
    modo_ejecucion: str  # "Producción (Full DANE)" o "Muestra / Portafolio"
    mensaje: str


class SpatialDataEngine:
    """
    Motor Espacial y Feature Store Integrado.
    Diseñado bajo principios de baja latencia (Low-Latency Spatial Pruning)
    y mínimo consumo de memoria I/O.
    """

    def __init__(self, forzar_modo_muestra: bool = False):
        self.usar_muestra = forzar_modo_muestra or not tiene_datos_completos()
        self.modo_str = "Muestra / Portafolio" if self.usar_muestra else "Producción (Full DANE)"
        self._df_bbox_municipios: Optional[pd.DataFrame] = None
        self._cache_particiones: Dict[str, gpd.GeoDataFrame] = {}
        self._gdf_muestra: Optional[gpd.GeoDataFrame] = None
        self._df_master_muestra: Optional[pd.DataFrame] = None

        logger.info(f"Inicializando SpatialDataEngine en modo: {self.modo_str}")
        self._cargar_indices()

    def _cargar_indices(self) -> None:
        """Carga en memoria los índices ultraligeros necesarios para el enrutamiento."""
        if RUTA_MUNICIPIOS_BBOX.exists():
            try:
                self._df_bbox_municipios = pd.read_parquet(RUTA_MUNICIPIOS_BBOX)
                logger.info(f"Índice Bounding Box cargado: {len(self._df_bbox_municipios)} municipios.")
            except Exception as e:
                logger.warning(f"No se pudo cargar municipios_bbox.parquet: {e}")

        # Si estamos en modo muestra, cargar datasets de muestra una sola vez
        if self.usar_muestra and tiene_datos_muestra():
            try:
                self._gdf_muestra = gpd.read_parquet(RUTA_MANZANAS_SAMPLE)
                self._df_master_muestra = pd.read_parquet(RUTA_MASTER_SAMPLE)
                logger.info(f"Dataset de muestra cargado: {len(self._gdf_muestra)} manzanas.")
            except Exception as e:
                logger.error(f"Error cargando datasets de muestra: {e}")

    def identificar_municipio(self, lat: float, lon: float) -> Optional[str]:
        """
        Identifica el código Divipola municipal usando Bounding Box search (O(1) / microsegundos).
        """
        if self._df_bbox_municipios is not None:
            candidatos = self._df_bbox_municipios[
                (self._df_bbox_municipios['minx'] <= lon) & (lon <= self._df_bbox_municipios['maxx']) &
                (self._df_bbox_municipios['miny'] <= lat) & (lat <= self._df_bbox_municipios['maxy'])
            ]
            if not candidatos.empty:
                # Retorna el primer candidato coincidente
                return str(candidatos.iloc[0]['mpio_cdpmp'])

        # Fallback a búsqueda en muestra
        if self._gdf_muestra is not None:
            punto = Point(lon, lat)
            match = self._gdf_muestra[self._gdf_muestra.geometry.contains(punto)]
            if not match.empty:
                return str(match.iloc[0]['mpio_cdpmp'])

        return None

    def _obtener_geometrias_municipio(self, codigo_mun: str) -> Optional[gpd.GeoDataFrame]:
        """Carga y cachea la partición de geometrías de un municipio específico."""
        if codigo_mun in self._cache_particiones:
            return self._cache_particiones[codigo_mun]

        if not self.usar_muestra:
            ruta_particion = RUTA_SEGMENTADOS_COMPLETA / f"manzanas_{codigo_mun}.parquet"
            if ruta_particion.exists():
                try:
                    # Column pruning para no sobrecargar RAM
                    gdf = gpd.read_parquet(ruta_particion, columns=COLUMNAS_GEOMETRIA)
                    self._cache_particiones[codigo_mun] = gdf
                    return gdf
                except Exception as e:
                    logger.error(f"Error leyendo partición {ruta_particion}: {e}")

        # Fallback a dataset de muestra
        if self._gdf_muestra is not None:
            gdf_filtro = self._gdf_muestra[self._gdf_muestra['mpio_cdpmp'] == codigo_mun]
            if not gdf_filtro.empty:
                return gdf_filtro

        return None

    def _consultar_features_maestro(self, manz_ccnct: str, codigo_mun: str) -> Dict[str, Any]:
        """
        Consulta las variables enriquecidas del maestro usando Predicate Pushdown de PyArrow.
        """
        if not self.usar_muestra and RUTA_MASTER_COMPLETA.exists():
            try:
                # Lectura ultra rápida con pushdown de predicado
                df = pd.read_parquet(
                    RUTA_MASTER_COMPLETA,
                    columns=COLUMNAS_NEGOCIO,
                    filters=[("manz_ccnct", "==", manz_ccnct)]
                )
                if not df.empty:
                    return df.iloc[0].to_dict()
            except Exception as e:
                logger.warning(f"Error en predicate pushdown de maestro: {e}")

        # Fallback a maestro de muestra
        if self._df_master_muestra is not None:
            df_match = self._df_master_muestra[self._df_master_muestra['manz_ccnct'].astype(str) == str(manz_ccnct)]
            if not df_match.empty:
                return df_match.iloc[0].to_dict()

        return {}

    def consultar_coordenada(self, lat: float, lon: float) -> EnrichedQueryResult:
        """
        Punto de entrada principal: orquesta el enriquecimiento sociodemográfico y económico
        de una coordenada geográfica con benchmarking de tiempo.
        """
        t_inicio = time.time()

        # 1. Validación de reglas de calidad de coordenadas en Colombia
        valido, error_coord = DataQualityValidator.validar_coordenada_en_colombia(lat, lon)
        if not valido:
            latencia = (time.time() - t_inicio) * 1000
            return EnrichedQueryResult(
                encontrado=False,
                latitud=lat,
                longitud=lon,
                manz_ccnct=None,
                codigo_divipola=None,
                municipio_nombre=None,
                departamento_nombre=None,
                area_m2=None,
                geometria=None,
                features={},
                calidad=None,
                latencia_ms=round(latencia, 2),
                modo_ejecucion=self.modo_str,
                mensaje=error_coord or "Coordenada fuera de límites"
            )

        # 2. Identificación rápida del municipio
        codigo_mun = self.identificar_municipio(lat, lon)
        if not codigo_mun:
            latencia = (time.time() - t_inicio) * 1000
            return EnrichedQueryResult(
                encontrado=False,
                latitud=lat,
                longitud=lon,
                manz_ccnct=None,
                codigo_divipola=None,
                municipio_nombre=None,
                departamento_nombre=None,
                area_m2=None,
                geometria=None,
                features={},
                calidad=None,
                latencia_ms=round(latencia, 2),
                modo_ejecucion=self.modo_str,
                mensaje="No se encontró cobertura urbana municipal para estas coordenadas."
            )

        # 3. Cargar partición municipal y realizar Point-in-Polygon (PiP)
        gdf_mun = self._obtener_geometrias_municipio(codigo_mun)
        if gdf_mun is None or gdf_mun.empty:
            latencia = (time.time() - t_inicio) * 1000
            return EnrichedQueryResult(
                encontrado=False,
                latitud=lat,
                longitud=lon,
                manz_ccnct=None,
                codigo_divipola=codigo_mun,
                municipio_nombre=None,
                departamento_nombre=None,
                area_m2=None,
                geometria=None,
                features={},
                calidad=None,
                latencia_ms=round(latencia, 2),
                modo_ejecucion=self.modo_str,
                mensaje=f"Partición municipal {codigo_mun} no disponible en disco."
            )

        punto = Point(lon, lat)
        match_manzana = gdf_mun[gdf_mun.geometry.contains(punto)]

        if match_manzana.empty:
            latencia = (time.time() - t_inicio) * 1000
            return EnrichedQueryResult(
                encontrado=False,
                latitud=lat,
                longitud=lon,
                manz_ccnct=None,
                codigo_divipola=codigo_mun,
                municipio_nombre=None,
                departamento_nombre=None,
                area_m2=None,
                geometria=None,
                features={},
                calidad=None,
                latencia_ms=round(latencia, 2),
                modo_ejecucion=self.modo_str,
                mensaje="El punto cae en el municipio pero fuera del polígono de una manzana urbana DANE."
            )

        fila_manzana = match_manzana.iloc[0]
        manz_ccnct = str(fila_manzana["manz_ccnct"])
        area_m2 = float(fila_manzana.get("manz_narea", 0.0))
        geometria = fila_manzana.geometry

        # 4. Enriquecimiento desde el Feature Store Maestro
        features = self._consultar_features_maestro(manz_ccnct, codigo_mun)

        # Asegurar variables básicas si no vinieron en maestro
        features["manz_ccnct"] = manz_ccnct
        features["mpio_cdpmp"] = codigo_mun
        features["manz_narea"] = area_m2

        # 5. Evaluación de Reglas de Calidad y Gobernanza
        serie_calidad = pd.Series(features)
        reporte_calidad = DataQualityValidator.evaluar_calidad_manzana(serie_calidad)

        # Nombres de departamento y municipio
        dpto_code = codigo_mun[:2]
        dpto_nombre = DEPARTAMENTOS_COLOMBIA.get(dpto_code, f"Dpto {dpto_code}")

        latencia = (time.time() - t_inicio) * 1000

        return EnrichedQueryResult(
            encontrado=True,
            latitud=lat,
            longitud=lon,
            manz_ccnct=manz_ccnct,
            codigo_divipola=codigo_mun,
            municipio_nombre=f"Municipio {codigo_mun}",
            departamento_nombre=dpto_nombre,
            area_m2=round(area_m2, 2),
            geometria=geometria,
            features=features,
            calidad=reporte_calidad,
            latencia_ms=round(latencia, 2),
            modo_ejecucion=self.modo_str,
            mensaje="Consulta y enriquecimiento completados exitosamente."
        )

    def generar_coordenada_aleatoria(self) -> Tuple[float, float]:
        """
        Genera una coordenada aleatoria garantizada dentro de un polígono urbano válido.
        """
        # Si hay particiones en caché, usar una
        gdf_objetivo = None
        if self._cache_particiones:
            gdf_objetivo = next(iter(self._cache_particiones.values()))
        elif self._gdf_muestra is not None:
            gdf_objetivo = self._gdf_muestra
        elif not self.usar_muestra and RUTA_NACIONAL_COMPLETA.exists():
            # Cargar Bogotá por defecto para generar rápidamente
            gdf_objetivo = self._obtener_geometrias_municipio("11001")

        if gdf_objetivo is None or gdf_objetivo.empty:
            # Coordenada representativa en Bogotá
            return 4.6766, -74.0531

        manzana = gdf_objetivo.sample(1).iloc[0]
        geom = manzana.geometry
        min_lon, min_lat, max_lon, max_lat = geom.bounds

        rng = random.SystemRandom()
        for _ in range(100):
            cand_lon = rng.uniform(min_lon, max_lon)  # nosec B311
            cand_lat = rng.uniform(min_lat, max_lat)  # nosec B311
            if geom.contains(Point(cand_lon, cand_lat)):
                return round(cand_lat, 6), round(cand_lon, 6)

        # Si el bucle falla por geometrías complejas, usar centroide
        centroid = geom.centroid
        return round(centroid.y, 6), round(centroid.x, 6)
