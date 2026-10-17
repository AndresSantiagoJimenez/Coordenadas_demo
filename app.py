"""
GeoDataIQ Colombia - Enterprise Geospatial Feature Store & Governance Dashboard.
Aplicación interactiva de analítica y enriquecimiento sociodemográfico por coordenadas.
Desarrollada para visualización de portafolio de Arquitectura e Ingeniería de Datos.
"""

import json
import logging
from typing import Dict, Any, Optional

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go

from src.config import (
    CIUDADES_PREDEFINIDAS,
    DEPARTAMENTOS_COLOMBIA,
    tiene_datos_completos
)
from src.engine import SpatialDataEngine, EnrichedQueryResult
from src.governance import DataGovernanceCatalog

# Configuración de página de Streamlit
st.set_page_config(
    page_title="GeoDataIQ | Enriquecimiento Geoespacial DANE",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para presentación de portafolio
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(120deg, #1E3A8A, #3B82F6, #10B981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #4B5563;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .badge-gov {
        background-color: #ECFDF5;
        color: #065F46;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        border: 1px solid #A7F3D0;
    }
    .badge-mode {
        background-color: #EFF6FF;
        color: #1E40AF;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        border: 1px solid #BFDBFE;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def obtener_motor_espacial(modo_muestra: bool) -> SpatialDataEngine:
    """Instancia y cachea el motor espacial de alta eficiencia."""
    return SpatialDataEngine(forzar_modo_muestra=modo_muestra)


def main():
    # Encabezado principal
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown('<div class="main-header">GeoDataIQ Colombia</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sub-header">Feature Store Geoespacial & Enrutamiento de Datos DANE a Escala Nacional</div>',
            unsafe_allow_html=True
        )
    with col_t2:
        st.markdown("""
        <div style="text-align: right; padding-top: 0.5rem;">
            <span class="badge-gov">🛡️ Gobierno & Calidad DANE</span><br>
            <span class="badge-mode" style="margin-top: 0.3rem;">⚡ Pushdown PyArrow</span>
        </div>
        """, unsafe_allow_html=True)

    # Sidebar: Parámetros de Control y Selección
    st.sidebar.image("https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Python-Dark.svg", width=40)
    st.sidebar.title("Configuración de Consulta")

    hay_full = tiene_datos_completos()
    modo_dataset = st.sidebar.radio(
        "Modo de Datos:",
        options=["Producción (541k Manzanas / 1,122 Mpios)" if hay_full else "Muestra (Portafolio / GitHub CI)", "Dataset de Muestra"],
        index=0
    )
    forzar_muestra = "Muestra" in modo_dataset

    # Instanciar el motor
    motor = obtener_motor_espacial(forzar_muestra)

    st.sidebar.markdown("---")
    st.sidebar.subheader("📍 Entrada de Coordenadas")

    metodo_entrada = st.sidebar.selectbox(
        "Método de Selección:",
        ["Ciudades Principales (Predefinidas)", "Entrada Manual (Lat/Lon)", "🎲 Coordenada Aleatoria"]
    )

    lat_init = 4.6766
    lon_init = -74.0531

    if metodo_entrada == "Ciudades Principales (Predefinidas)":
        ciudad_sel = st.sidebar.selectbox("Seleccione ubicación urbana:", list(CIUDADES_PREDEFINIDAS.keys()))
        lat_init = CIUDADES_PREDEFINIDAS[ciudad_sel]["lat"]
        lon_init = CIUDADES_PREDEFINIDAS[ciudad_sel]["lon"]

    elif metodo_entrada == "🎲 Coordenada Aleatoria":
        if st.sidebar.button("Generar Nueva Coordenada en Colombia", type="primary"):
            lat_init, lon_init = motor.generar_coordenada_aleatoria()
            st.session_state["lat_val"] = lat_init
            st.session_state["lon_val"] = lon_init
        else:
            lat_init = st.session_state.get("lat_val", 4.6766)
            lon_init = st.session_state.get("lon_val", -74.0531)

    lat_input = st.sidebar.number_input("Latitud:", value=float(lat_init), format="%.6f", step=0.0005)
    lon_input = st.sidebar.number_input("Longitud:", value=float(lon_init), format="%.6f", step=0.0005)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🗺️ Capas del Mapa")
    estilo_mapa = st.sidebar.selectbox(
        "Mapa Base:",
        ["CartoDB Positron (Limpio)", "OpenStreetMap", "Esri WorldImagery (Satélite)"]
    )

    tiles_dict = {
        "CartoDB Positron (Limpio)": "CartoDB positron",
        "OpenStreetMap": "OpenStreetMap",
        "Esri WorldImagery (Satélite)": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    }

    # Ejecutar la consulta en el motor espacial
    with st.spinner("Enrutando espacialmente y extrayendo features..."):
        resultado = motor.consultar_coordenada(lat=lat_input, lon=lon_input)

    # Banner de Estado y Desempeño
    col_b1, col_b2, col_b3, col_b4 = st.columns([3, 2, 2, 2])
    with col_b1:
        if resultado.encontrado:
            st.success(f"✅ Manzana Localizada: `{resultado.manz_ccnct}`")
        else:
            st.warning(f"⚠️ {resultado.mensaje}")
    with col_b2:
        st.info(f"⏱️ **Latencia**: {resultado.latencia_ms} ms")
    with col_b3:
        st.info(f"📂 **Modo**: {resultado.modo_ejecucion}")
    with col_b4:
        score_val = resultado.calidad.score_calidad if resultado.calidad else 0.0
        st.info(f"🛡️ **Calidad**: {score_val}%")

    # Layout Principal: Mapa y KPIs
    col_mapa, col_kpis = st.columns([7, 5])

    with col_mapa:
        st.markdown("##### 🗺️ Visualización Cartográfica e Isócrona (300m)")

        # Inicializar mapa Folium
        attr = "Esri" if "Esri" in estilo_mapa else None
        m = folium.Map(
            location=[lat_input, lon_input],
            zoom_start=16,
            tiles=tiles_dict[estilo_mapa],
            attr=attr
        )

        # Marcador del punto consultado
        folium.Marker(
            [lat_input, lon_input],
            tooltip="Coordenada Consultada",
            popup=f"Lat: {lat_input:.6f}<br>Lon: {lon_input:.6f}",
            icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")
        ).add_to(m)

        # Buffer de 300 metros de caminabilidad
        folium.Circle(
            radius=300,
            location=[lat_input, lon_input],
            color="#3B82F6",
            fill=True,
            fill_color="#3B82F6",
            fill_opacity=0.12,
            weight=1.5,
            tooltip="Buffer de Proximidad 300m (Caminabilidad)"
        ).add_to(m)

        # Renderizar polígono exacto de la manzana si se encontró
        if resultado.encontrado and resultado.geometria is not None:
            # Convertir geometría shapely a GeoJSON
            geo_json_data = {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": resultado.geometria.__geo_interface__,
                    "properties": {
                        "manz_ccnct": resultado.manz_ccnct,
                        "area_m2": resultado.area_m2
                    }
                }]
            }
            folium.GeoJson(
                geo_json_data,
                style_function=lambda x: {
                    "fillColor": "#10B981",
                    "color": "#059669",
                    "weight": 2.5,
                    "fillOpacity": 0.4
                },
                tooltip=f"Manzana DANE: {resultado.manz_ccnct}"
            ).add_to(m)

        # Renderizar componente de mapa
        st_folium(m, height=430, width="100%")

    with col_kpis:
        st.markdown("##### 📊 Indicadores Clave de la Manzana")
        feat = resultado.features if resultado.encontrado else {}

        k1, k2 = st.columns(2)
        with k1:
            st.metric(
                label="Área de Manzana",
                value=f"{resultado.area_m2 or 0:,.1f} m²"
            )
            st.metric(
                label="Unidades Económicas",
                value=int(feat.get("cnue_total_ue", 0) or 0)
            )
            estrato_bajo = float(feat.get("cnpv_pct_estrato_bajo", 0) or 0) * 100
            st.metric(
                label="% Estrato Bajo (1-2)",
                value=f"{estrato_bajo:.1f}%"
            )
        with k2:
            st.metric(
                label="Municipio / Divipola",
                value=f"{resultado.codigo_divipola or 'N/A'}"
            )
            dist_poi = float(feat.get("ovt_dist_min_m", 0) or 0)
            st.metric(
                label="Distancia POI Cercano",
                value=f"{dist_poi:.1f} m"
            )
            dist_gtfs = feat.get("gtfs_dist_parada_m")
            dist_gtfs_str = f"{float(dist_gtfs):.0f} m" if (dist_gtfs is not None and not pd.isna(dist_gtfs)) else "Sin Cobertura"
            st.metric(
                label="Parada Transporte Masivo",
                value=dist_gtfs_str
            )

    # Pestañas Analíticas Detalladas
    st.markdown("---")
    tab_comercio, tab_movilidad, tab_demo, tab_gov, tab_export = st.tabs([
        "🏪 Actividad Económica (CNUE)",
        "🚍 Movilidad & Accesibilidad",
        "👥 Demografía & Bienestar",
        "🛡️ Gobierno, Linaje & Calidad",
        "📥 Exportación de Datos"
    ])

    with tab_comercio:
        st.subheader("Mezcla Comercial y Comercio de Proximidad (DANE CNUE & Overture)")
        c_c1, c_c2 = st.columns(2)

        with c_c1:
            comercio_data = {
                "Categoría": ["Droguerías", "Panaderías", "Restaurantes", "Supermercados", "Cárnicos", "Licoreras"],
                "Cantidad": [
                    float(feat.get("cnue_n_drogueria", 0) or 0),
                    float(feat.get("cnue_n_panaderia", 0) or 0),
                    float(feat.get("cnue_n_restaurante", 0) or 0),
                    float(feat.get("cnue_n_super_tiendas", 0) or 0),
                    float(feat.get("cnue_n_carnicos", 0) or 0),
                    float(feat.get("cnue_n_licorera", 0) or 0)
                ]
            }
            df_com = pd.DataFrame(comercio_data)
            fig_bar = px.bar(
                df_com,
                x="Cantidad",
                y="Categoría",
                orientation="h",
                title="Comercios Censados en la Manzana (CNUE 2022)",
                color="Cantidad",
                color_continuous_scale="Blues"
            )
            fig_bar.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_bar, use_container_width=True)

        with c_c2:
            pois_300 = int(feat.get("ovt_n_poi_300m", 0) or 0)
            restbar_300 = int(feat.get("ovt_n_restbar_300m", 0) or 0)
            super_300 = int(feat.get("ovt_n_super_300m", 0) or 0)
            otros_poi = max(0, pois_300 - (restbar_300 + super_300))

            df_poi = pd.DataFrame({
                "Tipo": ["Restaurantes & Bares", "Supermercados", "Otros Comercios"],
                "Total": [restbar_300, super_300, otros_poi]
            })
            fig_pie = px.pie(
                df_poi,
                names="Tipo",
                values="Total",
                title=f"Densidad de POIs en Radio 300m (Total: {pois_300})",
                hole=0.45,
                color_discrete_sequence=["#3B82F6", "#10B981", "#94A3B8"]
            )
            fig_pie.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab_movilidad:
        st.subheader("Infraestructura Vial y Conectividad con Transporte Masivo")
        m_c1, m_c2 = st.columns(2)

        with m_c1:
            distancias = {
                "Tipo de Infraestructura": [
                    "Vía Secundaria",
                    "Vía Primaria",
                    "POI Más Próximo",
                    "Parada Transporte Masivo (GTFS)"
                ],
                "Distancia (m)": [
                    float(feat.get("via_dist_secundaria_m", 0) or 0),
                    float(feat.get("via_dist_primaria_m", 0) or 0),
                    float(feat.get("ovt_dist_min_m", 0) or 0),
                    float(feat.get("gtfs_dist_parada_m", 0) or 0) if feat.get("gtfs_dist_parada_m") is not None else 0
                ]
            }
            df_dist = pd.DataFrame(distancias)
            fig_dist = px.bar(
                df_dist,
                x="Tipo de Infraestructura",
                y="Distancia (m)",
                title="Distancias Mínimas a Redes de Movilidad y Servicios",
                color="Distancia (m)",
                color_continuous_scale="Viridis"
            )
            fig_dist.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_dist, use_container_width=True)

        with m_c2:
            st.markdown("##### Métricas de Conectividad de Red Vial")
            st.write(f"- **Jerarquía Vial Máxima (100m)**: `{feat.get('via_clase_max_100m', 'N/A')}`")
            st.write(f"- **Nodos Conectores a 50m**: `{feat.get('via_n_conectores_50m', 0)}`")
            st.write(f"- **Nodos Conectores a 100m**: `{feat.get('via_n_conectores_100m', 0)}`")
            st.write(f"- **Nodos Conectores a 300m**: `{feat.get('via_n_conectores_300m', 0)}`")
            gtfs_disp = feat.get("gtfs_disponible")
            estado_gtfs = "✅ Sistema Integrado Disponible" if gtfs_disp else "⚠️ Sin Cobertura GTFS Municipal"
            st.info(estado_gtfs)

    with tab_demo:
        st.subheader("Perfil Sociodemográfico y Caracterización de Vivienda (DANE CNPV)")
        d_c1, d_c2 = st.columns(2)

        with d_c1:
            educ_data = {
                "Nivel Educativo": ["Sin Educación", "Secundaria", "Superior / Universidad"],
                "Porcentaje": [
                    float(feat.get("cnpv_pct_sin_educ", 0) or 0) * 100,
                    float(feat.get("cnpv_pct_secundaria", 0) or 0) * 100,
                    float(feat.get("cnpv_pct_superior", 0) or 0) * 100
                ]
            }
            df_edu = pd.DataFrame(educ_data)
            fig_edu = px.bar(
                df_edu,
                x="Nivel Educativo",
                y="Porcentaje",
                title="Distribución de Nivel Educativo en la Manzana (%)",
                color="Nivel Educativo",
                color_discrete_sequence=["#EF4444", "#F59E0B", "#10B981"]
            )
            fig_edu.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_edu, use_container_width=True)

        with d_c2:
            st.markdown("##### Tipología de Hábitat y Dinámica")
            pct_internet = float(feat.get("cnpv_pct_con_internet", 0) or 0) * 100
            pct_apto = float(feat.get("cnpv_pct_apto", 0) or 0) * 100
            pct_cuarto = float(feat.get("cnpv_pct_cuarto", 0) or 0) * 100
            pct_mixto = float(feat.get("cnpv_pct_uso_mixto", 0) or 0) * 100

            st.write(f"- **Penetración de Internet**: `{pct_internet:.1f}%`")
            st.write(f"- **Viviendas en Apartamento**: `{pct_apto:.1f}%`")
            st.write(f"- **Viviendas en Cuarto / Inquilinato**: `{pct_cuarto:.1f}%`")
            st.write(f"- **Predios con Uso Mixto (Residencial + Comercial)**: `{pct_mixto:.1f}%`")
            st.write(f"- **Delta de Crecimiento de Viviendas (2018-2025)**: `{feat.get('viv_delta_2018_2025', 0)}`")

    with tab_gov:
        st.subheader("Auditoría de Gobierno del Dato, Linaje y Reglas de Calidad")
        g_c1, g_c2 = st.columns(2)

        with g_c1:
            st.markdown("##### 📋 Reporte de Validación de Calidad (Data Quality Score)")
            if resultado.calidad:
                st.write(f"- **Score Global**: `{resultado.calidad.score_calidad}%`")
                st.write(f"- **Reglas Verificadas**: `{resultado.calidad.checks_totales}`")
                st.write(f"- **Reglas Aprobadas**: `{resultado.calidad.checks_aprobados}`")

                if resultado.calidad.errores:
                    st.error("Errores Detectados: " + ", ".join(resultado.calidad.errores))
                else:
                    st.success("✅ Cero violaciones de integridad referencial o sintaxis.")

                if resultado.calidad.alertas:
                    st.warning("Observaciones: " + "; ".join(resultado.calidad.alertas))
            else:
                st.info("Sin evaluación de calidad disponible para esta coordenada.")

            st.markdown("##### 🔒 Cumplimiento Normativo y Privacidad")
            st.write("- **Ley 1581 de 2012 (Habeas Data)**: Cumplido. La plataforma no maneja datos de identificación personal (PII).")
            st.write("- **Ley 79 de 1993 y Ley 2335 de 2023 (DANE)**: Principio de Reserva y Secreto Estadístico preservado mediante agregación a nivel manzana.")

        with g_c2:
            st.markdown("##### 🧬 Linaje de Datos de la Manzana")
            fuentes = DataGovernanceCatalog.FUENTES_LINAJE
            for key, val in fuentes.items():
                with st.expander(f"📌 {val['nombre']}"):
                    st.write(f"- **Entidad Custodia**: {val['entidad']}")
                    st.write(f"- **Tipo de Capa**: {val['tipo']}")
                    st.write(f"- **Licencia**: {val['licencia']}")
                    st.write(f"- **Frecuencia**: {val['frecuencia']}")

    with tab_export:
        st.subheader("Exportación de Datos para Interoperabilidad")
        if resultado.encontrado:
            # Preparar diccionario serializable
            datos_export = dict(resultado.features)
            datos_export["latitud_consulta"] = lat_input
            datos_export["longitud_consulta"] = lon_input
            datos_export["manz_ccnct"] = resultado.manz_ccnct
            datos_export["latencia_ms"] = resultado.latencia_ms

            json_str = json.dumps(datos_export, indent=2, default=str)
            df_export = pd.DataFrame([datos_export])
            csv_str = df_export.to_csv(index=False)

            e_c1, e_c2 = st.columns(2)
            with e_c1:
                st.download_button(
                    label="📥 Descargar Perfil en JSON",
                    data=json_str,
                    file_name=f"manzana_{resultado.manz_ccnct}.json",
                    mime="application/json"
                )
            with e_c2:
                st.download_button(
                    label="📥 Descargar Perfil en CSV",
                    data=csv_str,
                    file_name=f"manzana_{resultado.manz_ccnct}.csv",
                    mime="text/csv"
                )

            st.markdown("##### Vista Previa Tabular:")
            st.dataframe(df_export.head(), use_container_width=True)
        else:
            st.warning("No hay datos disponibles para exportar con la coordenada actual.")


if __name__ == "__main__":
    main()
