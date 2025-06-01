import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from src.filter_utils import apply_filters
from src.kpi_utils import driver_kpis, _compute_kpi
import numpy as np
from src.global_filters import render_sidebar
from src.visualizations import render_heatmap, render_driver_bar, render_bubble_chart

# Título principal de la página
st.title("🧠 Root Cause Analysis")

# Cargar datos del estado de sesión
df = st.session_state.get("df")

# Renderizar la barra lateral de filtros y obtener configuración
filters = render_sidebar(df)

# Aplicar filtros definidos por el usuario
filtered_df, prev_df, error = apply_filters(df, filters)

# Si ocurre un error al aplicar filtros (ej. falta de datos previos)
if error:
    st.warning(error)

else:
    # === 1. MATRIZ DE CALOR (HEATMAP) ===========================
    st.subheader("🔍 1. Heatmap Matrix")

    # Columnas disponibles para análisis cruzado
    cols = [
        'country_name','hour', 'day_of_week', 'is_weekend',
        'hora_pico_ordenes', 'hora_pico_atd', 'hour_bin',
        'courier_flow', 'geo_archetype', 'merchant_surface',
        'region', 'territory', 'driver_experience'
    ]

    # Selección de ejes del heatmap
    x_col = st.selectbox("X Axis", cols, index=cols.index("hour"))
    y_col = st.selectbox("Y Axis", cols, index=cols.index("day_of_week"))

    # Validación: no permitir que X e Y sean iguales
    if y_col == x_col:
        st.warning("Y Axis cannot be the same as X Axis. Defaulting to 'day_of_week'.")
        y_col = "day_of_week"

    # Diccionario con opciones de KPI y sus equivalencias en el DataFrame
    kpi_choices = {
        "Median ATD": "median_ATD",
        "% Breaches": "pct_breaches",
        "P95 ATD": "p95_ATD",
        "Total Orders": "total_orders",
        "Breach Cost": "breach_cost",
        "Over/Under Pred": "over_under",
        'pickup_distance': 'pickup_distance',
        'dropoff_distance': 'dropoff_distance'
    }

    # Selección del KPI a visualizar en el heatmap
    val_display = st.selectbox("KPI to display", list(kpi_choices.keys()), index=0)
    kpi_col = kpi_choices[val_display]

    # Renderizar el heatmap con los parámetros seleccionados
    render_heatmap(filtered_df, x_col, y_col, val_display, kpi_col, filters["sla"], filters["cost_per_min"])

    # === 2. EXPLORADOR DE DESEMPEÑO POR CONDUCTOR ===============
    st.subheader("🚴 2. Driver Performance Explorer")

    # Selección del KPI por el cual rankear conductores
    selected_kpi = st.selectbox("Rank by KPI", [
        "median_ATD", "pct_breaches", "p95_ATD",
        "total_orders", "breach_cost", "over_under"
    ], index=0)

    # Tipo de ranking a mostrar (mejores o peores)
    rank_type = st.radio("Show:", ["Top 15", "Bottom 15"], horizontal=True)

    # Renderiza gráfico de barras y devuelve tabla con top conductores
    top_drivers = render_driver_bar(filtered_df, filters, selected_kpi, rank_type)

    # Tabla expandible con detalle completo de los conductores mostrados
    with st.expander("📋 Full KPI Table"):
        st.dataframe(top_drivers)

    # === 3. GRÁFICO DE BURBUJAS DE KPIs =========================
    st.subheader("📊 KPI Bubble Chart")

    # Selección de ejes para el gráfico de burbujas
    x_kpi = st.selectbox("X Axis KPI", list(kpi_choices.keys()), index=0)
    y_kpi = st.selectbox("Y Axis KPI", list(kpi_choices.keys()), index=1)

    # Habilitar o no tamaño variable de burbujas
    size_enabled = st.checkbox("Use Bubble Size?", value=False)

    # Selección de KPI para el tamaño de la burbuja (si aplica)
    size_kpi = st.selectbox("Bubble Size KPI", list(kpi_choices.keys()), index=2) if size_enabled else None

    # Validaciones para evitar conflictos con burbujas
    if size_kpi == "Over/Under Pred":
        st.warning("Over/Under Pred is not suitable for bubble size. Defaulting to 'Total Orders'")
        size_kpi = "Total Orders"
    elif size_kpi == x_kpi or size_kpi == y_kpi:
        st.warning("Bubble Size KPI cannot be the same as X or Y Axis. Defaulting to 'Total Orders'.")
        size_kpi = "Total Orders"

    if x_kpi == y_kpi:
        st.warning("X Axis KPI cannot be the same as Y Axis. Defaulting to 'Median ATD'.")
        x_kpi = "Median ATD"

    # Selección de categoría por la cual agrupar las burbujas
    category_col = st.selectbox("Group by (Bubble Category)", [
        "territory", "region", "geo_archetype",
        "driver_experience", 'courier_flow', 'merchant_surface'
    ])

    # Renderizar gráfico de burbujas con o sin tamaño variable
    if size_enabled:
        render_bubble_chart(df, kpi_choices[x_kpi], kpi_choices[y_kpi],
                            size_enabled, kpi_choices[size_kpi], category_col, filters)
    else:
        render_bubble_chart(df, kpi_choices[x_kpi], kpi_choices[y_kpi],
                            None, None, category_col, filters)
