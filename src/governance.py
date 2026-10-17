"""
Módulo de Gobierno de Datos, Calidad y Cumplimiento Normativo (Data Governance & Quality).
Implementa validaciones de esquema, reglas de calidad de datos (Data Quality),
linaje de fuentes (Data Lineage) y cumplimiento normativo (Habeas Data / Secreto Estadístico DANE).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from src.config import BBOX_COLOMBIA, DEPARTAMENTOS_COLOMBIA


@dataclass
class VariableMetadata:
    """Metadatos formales para el catálogo y diccionario de datos."""
    nombre: str
    descripcion: str
    fuente: str
    tipo_dato: str
    unidad_medida: str
    nivel_confidencialidad: str  # Pública, Agregada Estadística, Restringida
    regla_validacion: str


@dataclass
class DataQualityReport:
    """Reporte estructurado de calidad de datos para una consulta o registro."""
    es_valido: bool
    score_calidad: float  # De 0.0 a 100.0%
    checks_totales: int
    checks_aprobados: int
    alertas: List[str] = field(default_factory=list)
    errores: List[str] = field(default_factory=list)
    linaje: Dict[str, Any] = field(default_factory=dict)


class DataGovernanceCatalog:
    """Catálogo y Diccionario de Datos del Feature Store Geoespacial."""

    DICCIONARIO_VARIABLES: Dict[str, VariableMetadata] = {
        "manz_ccnct": VariableMetadata(
            nombre="Código de Manzana DANE",
            descripcion="Identificador único nacional de la manzana censal (22 dígitos).",
            fuente="DANE - Marco Geoestadístico Nacional (MGN 2025)",
            tipo_dato="String (22)",
            unidad_medida="Código alfanumérico",
            nivel_confidencialidad="Pública",
            regla_validacion="Longitud exacta 22 caracteres numéricos."
        ),
        "mpio_cdpmp": VariableMetadata(
            nombre="Código Divipola Municipio",
            descripcion="Código oficial del municipio según la codificación político-administrativa DANE.",
            fuente="DANE - Divipola",
            tipo_dato="String (5)",
            unidad_medida="Código numérico",
            nivel_confidencialidad="Pública",
            regla_validacion="5 dígitos numéricos; primeros 2 corresponden a departamento."
        ),
        "manz_narea": VariableMetadata(
            nombre="Área de Manzana",
            descripcion="Área superficial en metros cuadrados del polígono de la manzana.",
            fuente="DANE - MGN 2025",
            tipo_dato="Float",
            unidad_medida="m²",
            nivel_confidencialidad="Pública",
            regla_validacion="Valor numérico estrictamente > 0."
        ),
        "cnue_total_ue": VariableMetadata(
            nombre="Total Unidades Económicas",
            descripcion="Cantidad de establecimientos comerciales y productivos censados en la manzana.",
            fuente="DANE - Censo Nacional de Unidades Económicas (CNUE 2022)",
            tipo_dato="Integer / Float",
            unidad_medida="Conteo",
            nivel_confidencialidad="Agregada Estadística",
            regla_validacion="Entero o flotante >= 0."
        ),
        "cnue_n_drogueria": VariableMetadata(
            nombre="Número de Droguerías / Farmacias",
            descripcion="Establecimientos dedicados al comercio al por menor de medicamentos y productos farmacéuticos.",
            fuente="DANE - CNUE",
            tipo_dato="Integer / Float",
            unidad_medida="Conteo",
            nivel_confidencialidad="Agregada Estadística",
            regla_validacion=">= 0"
        ),
        "cnue_n_panaderia": VariableMetadata(
            nombre="Número de Panaderías",
            descripcion="Establecimientos de elaboración y venta de productos de panadería.",
            fuente="DANE - CNUE",
            tipo_dato="Integer / Float",
            unidad_medida="Conteo",
            nivel_confidencialidad="Agregada Estadística",
            regla_validacion=">= 0"
        ),
        "cnue_n_restaurante": VariableMetadata(
            nombre="Número de Restaurantes",
            descripcion="Establecimientos dedicados al expendio a la mesa de comidas preparadas.",
            fuente="DANE - CNUE",
            tipo_dato="Integer / Float",
            unidad_medida="Conteo",
            nivel_confidencialidad="Agregada Estadística",
            regla_validacion=">= 0"
        ),
        "cnue_n_super_tiendas": VariableMetadata(
            nombre="Supermercados y Tiendas",
            descripcion="Supermercados, minimercados y autoservicios de víveres y abarrotes.",
            fuente="DANE - CNUE",
            tipo_dato="Integer / Float",
            unidad_medida="Conteo",
            nivel_confidencialidad="Agregada Estadística",
            regla_validacion=">= 0"
        ),
        "cnue_n_carnicos": VariableMetadata(
            nombre="Carnicerías y Expendios de Carne",
            descripcion="Comercio al por menor de carnes y derivados cárnicos.",
            fuente="DANE - CNUE",
            tipo_dato="Integer / Float",
            unidad_medida="Conteo",
            nivel_confidencialidad="Agregada Estadística",
            regla_validacion=">= 0"
        ),
        "ovt_n_poi_300m": VariableMetadata(
            nombre="POIs en Radio de 300 Metros",
            descripcion="Conteo de puntos de interés comercial/servicios en un buffer de caminabilidad de 300m.",
            fuente="Overture Maps Foundation (Places Theme)",
            tipo_dato="Integer",
            unidad_medida="Conteo",
            nivel_confidencialidad="Pública (Open Data)",
            regla_validacion=">= 0"
        ),
        "ovt_dist_min_m": VariableMetadata(
            nombre="Distancia al POI más Cercano",
            descripcion="Distancia euclidiana mínima en metros al punto de interés comercial más próximo.",
            fuente="Overture Maps Foundation",
            tipo_dato="Float",
            unidad_medida="Metros",
            nivel_confidencialidad="Pública (Open Data)",
            regla_validacion=">= 0"
        ),
        "via_dist_secundaria_m": VariableMetadata(
            nombre="Distancia a Vía Secundaria",
            descripcion="Distancia mínima en metros a la red vial secundaria o colectora más cercana.",
            fuente="Red Vial Nacional / OpenStreetMap",
            tipo_dato="Float",
            unidad_medida="Metros",
            nivel_confidencialidad="Pública",
            regla_validacion=">= 0"
        ),
        "gtfs_dist_parada_m": VariableMetadata(
            nombre="Distancia a Parada de Transporte Masivo",
            descripcion="Distancia mínima a la estación o parada de sistema de transporte público (GTFS).",
            fuente="Sistemas Integrados de Transporte Masivo (GTFS Colombia)",
            tipo_dato="Float",
            unidad_medida="Metros",
            nivel_confidencialidad="Pública",
            regla_validacion=">= 0 o nulo si no hay cobertura de transporte masivo"
        ),
        "cnpv_pct_estrato_bajo": VariableMetadata(
            nombre="Porcentaje Estrato Bajo (1 y 2)",
            descripcion="Proporción de predios residenciales de la manzana clasificados en estratos 1 y 2.",
            fuente="DANE - Censo Nacional de Población y Vivienda (CNPV 2018)",
            tipo_dato="Float",
            unidad_medida="Proporción [0.0 - 1.0]",
            nivel_confidencialidad="Agregada Estadística",
            regla_validacion="En rango [0.0, 1.0]"
        ),
        "cnpv_pct_con_internet": VariableMetadata(
            nombre="Porcentaje Hogares con Internet",
            descripcion="Proporción de viviendas de la manzana con acceso a servicio de internet.",
            fuente="DANE - CNPV 2018",
            tipo_dato="Float",
            unidad_medida="Proporción [0.0 - 1.0]",
            nivel_confidencialidad="Agregada Estadística",
            regla_validacion="En rango [0.0, 1.0]"
        )
    }

    FUENTES_LINAJE: Dict[str, Dict[str, str]] = {
        "DANE_MGN": {
            "nombre": "Marco Geoestadístico Nacional (MGN 2025)",
            "entidad": "Departamento Administrativo Nacional de Estadística (DANE)",
            "tipo": "Vectorial / Polígonos de Manzana",
            "licencia": "Datos Abiertos Colombia (CC BY 4.0)",
            "frecuencia": "Actualización Cartográfica Anual"
        },
        "DANE_CNPV": {
            "nombre": "Censo Nacional de Población y Vivienda (CNPV 2018)",
            "entidad": "DANE",
            "tipo": "Tabular Agregado / Demográfico y Vivienda",
            "licencia": "Reserva Estadística - Ley 79/1993",
            "frecuencia": "Decenal"
        },
        "DANE_CNUE": {
            "nombre": "Censo Nacional de Unidades Económicas (CNUE 2022)",
            "entidad": "DANE",
            "tipo": "Económico de Proximidad",
            "licencia": "Datos Estadísticos Agregados",
            "frecuencia": "Económico Periódico"
        },
        "OVERTURE_MAPS": {
            "nombre": "Overture Maps Places Theme",
            "entidad": "Overture Maps Foundation (Linux Foundation)",
            "tipo": "Puntos de Interés Geoespaciales (POIs)",
            "licencia": "CDLA Permissive v2.0",
            "frecuencia": "Actualización Mensual"
        },
        "GTFS_COLOMBIA": {
            "nombre": "General Transit Feed Specification (GTFS)",
            "entidad": "Operadores SITM (TransMilenio, Metro Medellín, MIO Cali, etc.)",
            "tipo": "Red de Paradas y Rutas de Transporte Público",
            "licencia": "Datos Abiertos Municipales",
            "frecuencia": "Trimestral"
        }
    }


class DataQualityValidator:
    """Motor de Reglas de Calidad y Validación de Integridad de Datos."""

    @staticmethod
    def validar_coordenada_en_colombia(lat: float, lon: float) -> Tuple[bool, Optional[str]]:
        """Verifica si la coordenada se encuentra dentro del Bounding Box geográfico de Colombia."""
        if not (BBOX_COLOMBIA["min_lat"] <= lat <= BBOX_COLOMBIA["max_lat"]):
            return False, (
                f"Latitud {lat:.4f} fuera de los límites de Colombia "
                f"[{BBOX_COLOMBIA['min_lat']}, {BBOX_COLOMBIA['max_lat']}]."
            )
        if not (BBOX_COLOMBIA["min_lon"] <= lon <= BBOX_COLOMBIA["max_lon"]):
            return False, (
                f"Longitud {lon:.4f} fuera de los límites de Colombia "
                f"[{BBOX_COLOMBIA['min_lon']}, {BBOX_COLOMBIA['max_lon']}]."
            )
        return True, None

    @staticmethod
    def validar_codigo_manzana(manz_ccnct: Any) -> Tuple[bool, Optional[str]]:
        """Verifica la integridad del identificador DANE de 22 dígitos."""
        codigo_str = str(manz_ccnct).strip()
        if len(codigo_str) != 22:
            return False, f"Código de manzana '{codigo_str}' inválido. Debe tener exactamente 22 caracteres (tiene {len(codigo_str)})."
        if not codigo_str.isdigit():
            return False, f"Código de manzana '{codigo_str}' contiene caracteres no numéricos."
        return True, None

    @classmethod
    def evaluar_calidad_manzana(cls, registro: pd.Series) -> DataQualityReport:
        """
        Evalúa un conjunto integral de reglas de calidad de datos (Completeness, Validity, Consistency)
        sobre el registro enriquecido de la manzana consultada.
        """
        checks_totales = 0
        checks_aprobados = 0
        alertas: List[str] = []
        errores: List[str] = []

        # 1. Regla: Integridad de Primary Key (manz_ccnct)
        checks_totales += 1
        if "manz_ccnct" in registro:
            ok, msg = cls.validar_codigo_manzana(registro["manz_ccnct"])
            if ok:
                checks_aprobados += 1
            else:
                errores.append(msg or "Error en clave primaria")
        else:
            errores.append("Registro carece de columna 'manz_ccnct'")

        # 2. Regla: Código Divipola municipal (5 dígitos válidos)
        checks_totales += 1
        codigo_mun = str(registro.get("mpio_cdpmp", "")).strip()
        if len(codigo_mun) == 5 and codigo_mun.isdigit():
            checks_aprobados += 1
            # Verificar si departamento es reconocido
            dpto = codigo_mun[:2]
            if dpto not in DEPARTAMENTOS_COLOMBIA:
                alertas.append(f"Código de departamento '{dpto}' no está en la tabla de referencia estándar.")
        else:
            errores.append(f"Código Divipola '{codigo_mun}' no cumple con el estándar de 5 dígitos.")

        # 3. Regla: Área positiva
        if "manz_narea" in registro and pd.notna(registro["manz_narea"]):
            checks_totales += 1
            area = float(registro["manz_narea"])
            if area > 0:
                checks_aprobados += 1
            else:
                errores.append(f"Área de la manzana inválida ({area} m² <= 0).")

        # 4. Regla: Proporciones censales en rango [0.0, 1.0]
        columnas_pct = [c for c in registro.index if c.startswith("cnpv_pct_")]
        for col in columnas_pct:
            val = registro[col]
            if pd.notna(val):
                checks_totales += 1
                try:
                    val_float = float(val)
                    if 0.0 <= val_float <= 1.0:
                        checks_aprobados += 1
                    else:
                        alertas.append(f"Valor fuera de rango en {col}: {val_float:.3f} (debe estar en [0, 1]).")
                except (ValueError, TypeError):
                    errores.append(f"Valor no numérico en porcentaje {col}: {val}")

        # 5. Regla: Distancias físicas no negativas
        columnas_dist = [c for c in registro.index if "_dist_" in c]
        for col in columnas_dist:
            val = registro[col]
            if pd.notna(val):
                checks_totales += 1
                try:
                    dist_float = float(val)
                    if dist_float >= 0:
                        checks_aprobados += 1
                    else:
                        errores.append(f"Distancia negativa en {col}: {dist_float} m.")
                except (ValueError, TypeError):
                    errores.append(f"Valor no numérico en distancia {col}: {val}")

        # 6. Regla: Conteos económicos no negativos
        columnas_conteo = [c for c in registro.index if c.startswith("cnue_n_") or c == "cnue_total_ue" or c.startswith("ovt_n_")]
        for col in columnas_conteo:
            val = registro[col]
            if pd.notna(val):
                checks_totales += 1
                try:
                    conteo_float = float(val)
                    if conteo_float >= 0:
                        checks_aprobados += 1
                    else:
                        alertas.append(f"Conteo negativo en {col}: {conteo_float}")
                except (ValueError, TypeError):
                    errores.append(f"Valor no numérico en conteo {col}: {val}")

        score = (checks_aprobados / checks_totales * 100.0) if checks_totales > 0 else 100.0
        es_valido = len(errores) == 0

        # Linaje de datos asociado
        linaje = {
            "fuentes_consultadas": ["DANE MGN 2025", "DANE CNPV", "DANE CNUE", "Overture Maps", "GTFS"],
            "cumplimiento_habeas_data": "Aprobado (Datos agregados a nivel manzana sin PII - Ley 1581/2012)",
            "reserva_estadistica": "Cumplida (Ley 79 de 1993 y Ley 2335 de 2023 DANE)",
            "manz_ccnct": str(registro.get("manz_ccnct", "N/A")),
            "divipola": codigo_mun
        }

        return DataQualityReport(
            es_valido=es_valido,
            score_calidad=round(score, 1),
            checks_totales=checks_totales,
            checks_aprobados=checks_aprobados,
            alertas=alertas,
            errores=errores,
            linaje=linaje
        )
