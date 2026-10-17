"""
Módulo de pruebas para el enrutamiento dinámico espacial.
Verifica la generación de coordenadas y la búsqueda particionada.
"""

import os
import unittest
import pandas as pd
import geopandas as gpd

from src.geo_procesamiento import (
    generar_coordenada_aleatoria_colombia,
    identificar_municipio_por_coordenada,
    buscar_y_enriquecer_coordenada_dinamica
)

class TestEnrutamientoDinamico(unittest.TestCase):
    """Suite de pruebas para validar la búsqueda dinámica de manzanas."""
    @classmethod
    def setUpClass(cls):
        """Carga el mapa nacional y configura rutas relativas seguras."""
        print("\n⏳ Cargando Mapa Nacional (Toda Colombia)...")
        ruta_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        #ruta_shp = os.path.join(ruta_raiz, "DANE", "MGN2025_URB_MANZANA", "MGN_URB_MANZANA.shp")
        ruta_nacional = os.path.join(ruta_raiz, "Data", "DANE", "MGN2025_URB_MANZANA", "MGN_URB_MANZANA_CLEAN.parquet")
        #cls.ruta_segmentados = os.path.join(ruta_raiz, "DANE", "segmentado")
        cls.ruta_segmentados = os.path.join(ruta_raiz, "Data", "DANE", "segmentado_clean")
        cls.ruta_master = os.path.join(ruta_raiz, "Data", "features_mgn2025", 
                                       "features_mgn2025_master_clean.parquet")

        if not os.path.exists(ruta_nacional):
            raise FileNotFoundError(f"No se encontró el shapefile en: {ruta_nacional}")

        #cls.gdf_nacional = gpd.read_file(ruta_nacional)
        cls.gdf_nacional = gpd.read_parquet(ruta_nacional)
        print("✅ Entorno listo.")

    def test_identificar_municipio(self):
        """Prueba unitaria aislada para la extracción del código Divipola."""
        # Se genera una coordenada y se extrae su municipio sin cruzar datos pesados
        lat_col, lon_col = generar_coordenada_aleatoria_colombia(self.gdf_nacional)
        codigo_mun = identificar_municipio_por_coordenada(self.gdf_nacional, lat_col, lon_col)
        
        self.assertIsNotNone(codigo_mun)
        self.assertEqual(len(codigo_mun), 5, "El código Divipola debe tener exactamente 5 dígitos.")

    def test_flujo_completo_dinamico(self):
        """Prueba de integración: Genera, enruta, lee parquet y cruza."""
        lat_col, lon_col = generar_coordenada_aleatoria_colombia(self.gdf_nacional)
        print(f"\n-> Coordenada a buscar: {lat_col:.6f}, {lon_col:.6f}")

        resultado = buscar_y_enriquecer_coordenada_dinamica(
            lat=lat_col,
            lon=lon_col,
            gdf_nacional=self.gdf_nacional,
            ruta_segmentados=self.ruta_segmentados,
            ruta_master=self.ruta_master
        )

        if resultado is None:
            print("⚠️ El municipio se identificó, pero su archivo parquet no existe.")
        else:
            self.assertFalse(resultado.empty, "Se cargó el archivo pero no cruzó la manzana.")
            self.assertIn('manz_ccnct', resultado.columns, "Falta la columna maestra en el cruce.")

            # Formateo de salida limpia
            print("\n" + "="*50)
            print(f"📊 PERFIL DE LA MANZANA (Código: {resultado.iloc[0]['manz_ccnct']})")
            print("="*50)

            datos_manzana = resultado.iloc[0]
            for columna in datos_manzana.index:
                if columna != 'geometry':
                    valor = datos_manzana[columna]
                    if pd.isna(valor):
                        valor = "Sin Dato (Null)"
                    print(f" > {columna.ljust(25)}: {valor}")
            print("="*50 + "\n")


if __name__ == '__main__':
    unittest.main(verbosity=2)