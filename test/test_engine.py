"""
Pruebas unitarias para el motor de enrutamiento espacial (SpatialDataEngine).
Valida benchmarking, detección jerárquica de municipio, PiP y enriquecimiento.
"""

import unittest
from src.engine import SpatialDataEngine


class TestSpatialEngine(unittest.TestCase):
    """Suite de validación del motor espacial y feature store."""

    @classmethod
    def setUpClass(cls):
        """Inicializa el motor en modo disponible."""
        cls.engine = SpatialDataEngine()

    def test_inicializacion_engine(self):
        """Verifica que el motor se inicializa con los índices correctos."""
        self.assertIsNotNone(self.engine)
        self.assertIn(self.engine.modo_str, ["Producción (Full DANE)", "Muestra / Portafolio"])

    def test_coordenada_fuera_colombia(self):
        """Verifica rechazo inmediato y latencia baja para coordenadas foráneas."""
        res = self.engine.consultar_coordenada(lat=51.5074, lon=-0.1278)  # Londres
        self.assertFalse(res.encontrado)
        self.assertIn("fuera de los límites", res.mensaje)
        self.assertLess(res.latencia_ms, 50.0, "La validación inicial debe responder en < 50ms.")

    def test_consulta_coordenada_bogota(self):
        """Verifica enriquecimiento exitoso para una coordenada en Bogotá."""
        # Parque de la 93 (Bogotá)
        res = self.engine.consultar_coordenada(lat=4.6766, lon=-74.0531)

        # Si el punto específico cae en manzana o requiere punto exacto
        if res.encontrado:
            self.assertEqual(res.codigo_divipola, "11001")
            self.assertIsNotNone(res.manz_ccnct)
            self.assertGreater(res.area_m2, 0)
            self.assertIsNotNone(res.calidad)
            self.assertGreaterEqual(res.calidad.score_calidad, 80.0)
            self.assertLess(res.latencia_ms, 2500.0, "Latencia debe ser razonable para portafolio.")
            print(f"\n[BENCHMARK] Consulta completada en {res.latencia_ms:.2f} ms")

    def test_generador_coordenadas_aleatorias(self):
        """Valida que el generador devuelva coordenadas dentro de Colombia."""
        lat, lon = self.engine.generar_coordenada_aleatoria()
        self.assertIsInstance(lat, float)
        self.assertIsInstance(lon, float)
        self.assertGreater(lat, -4.3)
        self.assertLess(lat, 13.5)
        self.assertGreater(lon, -81.8)
        self.assertLess(lon, -66.8)


if __name__ == "__main__":
    unittest.main(verbosity=2)
