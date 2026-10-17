"""
Módulo de pruebas para el enrutamiento dinámico espacial.
Verifica la generación de coordenadas y la búsqueda particionada tanto en modo producción como muestra.
"""

import os
import sys
import unittest
import pandas as pd
import geopandas as gpd

# Asegurar codificación utf-8 en salidas de consola
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.geo_procesamiento import (
    generar_coordenada_aleatoria_colombia,
    identificar_municipio_por_coordenada,
    buscar_y_enriquecer_coordenada_dinamica
)
from src.config import (
    RUTA_NACIONAL_COMPLETA,
    RUTA_SEGMENTADOS_COMPLETA,
    RUTA_MASTER_COMPLETA,
    RUTA_MANZANAS_SAMPLE,
    RUTA_MASTER_SAMPLE,
    tiene_datos_completos
)


class TestEnrutamientoDinamico(unittest.TestCase):
    """Suite de pruebas para validar la búsqueda dinámica de manzanas."""

    @classmethod
    def setUpClass(cls):
        """Carga mapa y configura rutas relativas seguras con fallback a datos de muestra."""
        if tiene_datos_completos():
            print("\n[INFO] Cargando Mapa Nacional Completo (DANE)...")
            cls.ruta_segmentados = str(RUTA_SEGMENTADOS_COMPLETA)
            cls.ruta_master = str(RUTA_MASTER_COMPLETA)
            cls.gdf_nacional = gpd.read_parquet(RUTA_NACIONAL_COMPLETA)
            cls.modo = "Full"
        else:
            print("\n[INFO] Modo CI/Demo: Cargando Dataset de Muestra...")
            cls.ruta_segmentados = os.path.dirname(str(RUTA_MANZANAS_SAMPLE))
            cls.ruta_master = str(RUTA_MASTER_SAMPLE)
            cls.gdf_nacional = gpd.read_parquet(RUTA_MANZANAS_SAMPLE)
            cls.modo = "Sample"

        print(f"[OK] Entorno listo en modo: {cls.modo} ({len(cls.gdf_nacional)} registros)")

    def test_identificar_municipio(self):
        """Prueba unitaria aislada para la extracción del código Divipola."""
        lat_col, lon_col = generar_coordenada_aleatoria_colombia(self.gdf_nacional)
        codigo_mun = identificar_municipio_por_coordenada(self.gdf_nacional, lat_col, lon_col)

        self.assertIsNotNone(codigo_mun, "No se pudo identificar el código de municipio.")
        self.assertEqual(len(codigo_mun), 5, "El código Divipola debe tener exactamente 5 dígitos.")
        self.assertTrue(codigo_mun.isdigit(), "El código Divipola debe ser estrictamente numérico.")

    def test_flujo_completo_dinamico(self):
        """Prueba de integración: Genera, enruta, lee parquet y cruza."""
        lat_col, lon_col = generar_coordenada_aleatoria_colombia(self.gdf_nacional)
        print(f"\n-> Coordenada a buscar: {lat_col:.6f}, {lon_col:.6f}")

        # En modo muestra, segmentados está en Data/DANE/segmentado_clean si existe, o probamos el cruce
        ruta_seg = str(RUTA_SEGMENTADOS_COMPLETA) if RUTA_SEGMENTADOS_COMPLETA.exists() else self.ruta_segmentados

        resultado = buscar_y_enriquecer_coordenada_dinamica(
            lat=lat_col,
            lon=lon_col,
            gdf_nacional=self.gdf_nacional,
            ruta_segmentados=ruta_seg,
            ruta_master=self.ruta_master
        )

        if resultado is None:
            print("[WARN] Municipio identificado pero la partición no existe localmente.")
        else:
            self.assertFalse(resultado.empty, "Se cargó el archivo pero no cruzó la manzana.")
            self.assertIn("manz_ccnct", resultado.columns, "Falta la columna maestra 'manz_ccnct' en el cruce.")

            # Validación de salida estructurada
            print("\n" + "=" * 50)
            print(f"[RESUMEN] PERFIL DE LA MANZANA (Codigo: {resultado.iloc[0]['manz_ccnct']})")
            print("=" * 50)

            datos_manzana = resultado.iloc[0]
            for columna in datos_manzana.index:
                if columna != "geometry":
                    valor = datos_manzana[columna]
                    if pd.isna(valor):
                        valor = "Sin Dato (Null)"
                    print(f" > {columna.ljust(25)}: {valor}")
            print("=" * 50 + "\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)