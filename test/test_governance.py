"""
Pruebas unitarias para el módulo de Gobierno y Calidad de Datos (Data Governance).
Valida reglas de calidad, catálogo de metadatos, integridad de claves y Habeas Data.
"""

import unittest
import pandas as pd
from src.governance import DataQualityValidator, DataGovernanceCatalog, DataQualityReport


class TestDataGovernance(unittest.TestCase):
    """Suite de validación de reglas de calidad y gobernanza."""

    def test_catalogo_metadatos_completo(self):
        """Verifica que el catálogo contiene las variables fundamentales y sus fuentes."""
        diccionario = DataGovernanceCatalog.DICCIONARIO_VARIABLES
        fuentes = DataGovernanceCatalog.FUENTES_LINAJE

        self.assertIn("manz_ccnct", diccionario)
        self.assertIn("mpio_cdpmp", diccionario)
        self.assertIn("cnue_total_ue", diccionario)
        self.assertIn("gtfs_dist_parada_m", diccionario)
        self.assertIn("cnpv_pct_estrato_bajo", diccionario)

        # Verificar fuentes oficiales
        self.assertIn("DANE_MGN", fuentes)
        self.assertIn("DANE_CNPV", fuentes)
        self.assertIn("DANE_CNUE", fuentes)
        self.assertIn("OVERTURE_MAPS", fuentes)
        self.assertIn("GTFS_COLOMBIA", fuentes)

    def test_validador_coordenadas_colombia(self):
        """Valida que el bounding box de Colombia acepte puntos válidos y rechace inválidos."""
        # Coordenada válida en Bogotá
        ok, msg = DataQualityValidator.validar_coordenada_en_colombia(4.6766, -74.0531)
        self.assertTrue(ok)
        self.assertIsNone(msg)

        # Coordenada en París (fuera de Colombia)
        ok, msg = DataQualityValidator.validar_coordenada_en_colombia(48.8566, 2.3522)
        self.assertFalse(ok)
        self.assertIsNotNone(msg)

        # Coordenada en Tokio (fuera de Colombia)
        ok, msg = DataQualityValidator.validar_coordenada_en_colombia(35.6762, 139.6503)
        self.assertFalse(ok)

    def test_validador_codigo_manzana(self):
        """Valida las reglas sintácticas del identificador nacional DANE de 22 dígitos."""
        # Código válido de 22 dígitos
        codigo_valido = "1100110000000005060221"
        ok, msg = DataQualityValidator.validar_codigo_manzana(codigo_valido)
        self.assertTrue(ok)
        self.assertIsNone(msg)

        # Código de longitud errónea (21 dígitos)
        codigo_corto = "110011000000000506022"
        ok, msg = DataQualityValidator.validar_codigo_manzana(codigo_corto)
        self.assertFalse(ok)
        self.assertIn("22 caracteres", msg)

        # Código con letras
        codigo_letras = "110011000000000506022A"
        ok, msg = DataQualityValidator.validar_codigo_manzana(codigo_letras)
        self.assertFalse(ok)
        self.assertIn("no numéricos", msg)

    def test_evaluacion_calidad_registro_perfecto(self):
        """Evalúa un registro con todos los datos coherentes (Score = 100%)."""
        registro = pd.Series({
            "manz_ccnct": "1100110000000005060221",
            "mpio_cdpmp": "11001",
            "manz_narea": 4500.5,
            "cnpv_pct_estrato_bajo": 0.35,
            "cnpv_pct_con_internet": 0.88,
            "ovt_dist_min_m": 85.0,
            "via_dist_secundaria_m": 42.0,
            "cnue_total_ue": 12.0,
            "cnue_n_drogueria": 2.0
        })

        reporte = DataQualityValidator.evaluar_calidad_manzana(registro)
        self.assertTrue(reporte.es_valido)
        self.assertEqual(reporte.score_calidad, 100.0)
        self.assertEqual(len(reporte.errores), 0)
        self.assertIn("cumplimiento_habeas_data", reporte.linaje)

    def test_evaluacion_calidad_con_anomalias(self):
        """Evalúa un registro con anomalías en porcentajes y distancias."""
        registro = pd.Series({
            "manz_ccnct": "1100110000000005060221",
            "mpio_cdpmp": "11001",
            "manz_narea": 4500.5,
            "cnpv_pct_estrato_bajo": 1.5,  # Fuera de rango [0, 1]
            "ovt_dist_min_m": -10.0,       # Distancia negativa inválida
            "cnue_total_ue": 5.0
        })

        reporte = DataQualityValidator.evaluar_calidad_manzana(registro)
        self.assertFalse(reporte.es_valido)
        self.assertLess(reporte.score_calidad, 100.0)
        self.assertTrue(any("Distancia negativa" in err for err in reporte.errores))
        self.assertTrue(any("fuera de rango" in alert for alert in reporte.alertas))


if __name__ == "__main__":
    unittest.main(verbosity=2)
