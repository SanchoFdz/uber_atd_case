import streamlit as st
import numpy as np
from src.filter_utils import apply_filters
from src.kpi_utils import calculate_kpis, zone_kpis, trend_kpis
from src.global_filters import render_sidebar
from src.style_utils import format_number
from src.visualizations import build_zone_map
from streamlit_folium import st_folium

# Obtener datasets previamente cargados desde el estado de sesión
df = st.session_state.get("df")
gdf = st.session_state.get("gdf")

# Renderiza la barra lateral de filtros y guarda resultados en `filters`
filters = render_sidebar(df)

# Título de la aplicación
st.title("📊 Conversation Openers")

# Recupera los filtros del estado de sesión
filters = st.session_state.get("filters", {})

# Si no hay filtros definidos, muestra advertencia
if not filters:
    st.warning("Please set filters in the sidebar.")

else:
    # Aplica los filtros al dataset principal y genera el subconjunto de comparación
    filtered_df, prev_df, error = apply_filters(df, filters)

    if error:
        # Si no hay suficiente data para el periodo previo, muestra advertencia
        st.warning(error)
    else:
        # Calcula los KPIs principales comparando periodo actual vs anterior
        kpis = calculate_kpis(filtered_df, prev_df, filters["sla"], filters["cost_per_min"])

        # Despliega los KPIs en tarjetas de 3 columnas
        for i in range(0, len(kpis), 3):
            cols = st.columns(3)

            for j, (title, value, delta, move) in enumerate(kpis[i:i+3]):
                with cols[j]:
                    prev_val = value - delta

                    # Define color de la variación según tipo de KPI
                    if move == "reduce":
                        color = "red" if delta > 0 else "green"
                    if move == "increase":
                        color = "green" if delta < 0 else "red"
                    if delta == 0:
                        color = "gray"

                    # Calcular % delta respecto al valor anterior
                    delta = 100 * (delta) / prev_val if prev_val != 0 else 0

                    # Formatear los valores para presentación
                    formatted_value = format_number(value, is_currency="Cost" in title)
                    formatted_prev = format_number(prev_val, is_currency="Cost" in title)

                    # Mostrar tarjeta personalizada con HTML
                    st.markdown(f"""
                    <div class="kpi-card">
                        <h5 style="text-align:center;">{title}</h5>
                        <h2 style="text-align:center;">{formatted_value}</h2>
                        <p style="text-align:center; font-size:0.8em; color:{color};">
                            Prev: {formatted_prev} ({delta:+.1f}%)
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

        # Selector para elegir el KPI a visualizar gráficamente
        kpi_column = st.selectbox("Select KPI to visualize",
            ["Median ATD", "P95 ATD", "% Breaches", "Total Orders", "Breach Cost", "Over/Under Pred"]
        )

        # Mapeo entre label del selector y nombre de columna en el DataFrame
        filter_map = {
            "Median ATD": "median_ATD",
            "P95 ATD": "p95_ATD",
            "% Breaches": "pct_breaches",
            "Total Orders": "total_orders",
            "Breach Cost": "breach_cost",
            "Over/Under Pred": "over_under"
        }

        st.subheader("📈 Rolling KPI Trends")

        # Validación de longitud del benchmark para aplicar rolling window
        if filters["benchmark_length"] <= 6:
            st.info("Please select at least 7 days to view rolling trends.")
        else:
            # Genera tendencias suavizadas por día para KPI actual y comparativo
            try:
                trend_df = trend_kpis(filtered_df, prev_df, filter_map[kpi_column],
                                    filters['sla'], filters['cost_per_min'])

                # Despliega gráfico de línea con series temporales
                st.line_chart(trend_df.set_index("date"), height=350, use_container_width=True)
            except:
                st.info("Not enough data points for that unique filter combination, please try out other filters.")

        # Mapa coroplético con colores por zona y KPI seleccionado
        st.subheader("🗺️ KPI Heatmap over Mexico City")
        try:
            # Calcular KPIs por territorio
            zone_df = zone_kpis(filtered_df, filters['sla'], filters['cost_per_min'])

            # Construir mapa con KPI seleccionado
            m = build_zone_map(zone_df, gdf, filter_map[kpi_column])

            # Renderizar mapa usando st_folium
            st_folium(m, use_container_width=True, height=400)
        
        except Exception as e:
            # En caso de error de renderización, mostrar advertencia
            st.info("Not enough data points for that unique filter combination, please try out other filters.")