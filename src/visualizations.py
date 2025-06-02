import os
import geopandas as gpd
import folium
from branca.colormap import LinearColormap
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium
from src.kpi_utils import driver_kpis, _compute_kpi
import plotly.io as pio

pio.templates["custom"] = go.layout.Template(
    layout_colorway=['#3FC060', 'black', 'white']
)

pio.templates.default = "custom"


def build_zone_map(zone_df,
                   gdf,
                   kpi_column):
    """
    Construye un mapa coroplético de zonas (territorios) con colores por KPI.

    Parameters
    ----------
    zone_df : pd.DataFrame
        DataFrame con métricas por territorio.
    gdf : gpd.GeoDataFrame
        GeoDataFrame con geometrías (shapes) por territorio.
    kpi_column : str
        Nombre del KPI a visualizar (debe estar en zone_df).

    Returns
    -------
    folium.Map
        Mapa interactivo con tooltip detallado y escala de color según el KPI.
    """
    
    
    df = (gdf.copy()).merge(zone_df.copy(), on="territory", how="left") \
                   .dropna(subset=["territory"])


    kpi_goal = {
        "median_ATD": False,
        "p95_ATD":   False,
        "pct_breaches": False,
        "breach_cost":  False,
        "over_under":   False,
        "total_orders": True,
    }

    ascending = kpi_goal.get(kpi_column, False)

    valid = df[kpi_column].dropna()
    vmin, vmax = valid.min(), valid.max()

    cmap = LinearColormap(
        colors = ['red', 'yellow', 'green'] if ascending
                 else ['green', 'yellow', 'red'],
        vmin   = vmin,
        vmax   = vmax
    )

    # --- construir mapa -----------------------------------------------------
    m = folium.Map(location=[19.4326, -99.1332],
                   zoom_start=11,
                   tiles="cartodbpositron")

    for _, row in df.iterrows():
        color = cmap(row[kpi_column]) if pd.notna(row[kpi_column]) else "lightgray"

        tooltip = folium.Tooltip(f"""
            <b>{row.get('NOM_MUN', 'Unknown')}</b><br>
            <b>Median ATD:</b> {row.get('median_ATD', float('nan')):.2f}<br>
            <b>P95 ATD:</b> {row.get('p95_ATD', float('nan')):.2f}<br>
            <b>% Breaches:</b> {row.get('pct_breaches', float('nan')):.2f}%<br>
            <b>Total Orders:</b> {int(row.get('total_orders', 0)):,}<br>
            <b>Breach Cost:</b> ${row.get('breach_cost', 0):,.0f}<br>
            <b>Over/Under Pred:</b> {row.get('over_under', 0):+.2f}
        """, sticky=True)

        folium.GeoJson(
            row["geometry"],
            style_function=lambda _, col=color: {
                "fillColor": col,
                "color": "black",
                "weight": 0.5,
                "fillOpacity": 0.7,
            },
            tooltip=tooltip
        ).add_to(m)

    cmap.caption = f"{kpi_column} ({'higher is better' if ascending else 'lower is better'})"
    cmap.add_to(m)

    return m

def render_heatmap(filtered_df,x_col, y_col, val_display, kpi_col, sla, cost_per_min):
    """
    Renderiza un heatmap de un KPI en función de dos variables categóricas (ejes X y Y).

    Parameters
    ----------
    filtered_df : pd.DataFrame
        Dataset filtrado a analizar.
    x_col : str
        Columna a usar en el eje X (por ejemplo, 'hour').
    y_col : str
        Columna a usar en el eje Y (por ejemplo, 'day_of_week').
    val_display : str
        Título amigable del KPI (para el título del gráfico).
    kpi_col : str
        Nombre del KPI a calcular (usa `_compute_kpi` si aplica).
    sla : float
        SLA en minutos para cálculo de incumplimientos.
    cost_per_min : float
        Penalización monetaria por incumplimiento.

    Returns
    -------
    None
        El heatmap se renderiza directamente en la interfaz con `st.pyplot`.
    """

    day_map = {
            0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu",
            4: "Fri", 5: "Sat", 6: "Sun"
        }
    
    label_mapper = {
        "day_of_week": day_map,
    }

    x_vals = filtered_df[x_col].dropna().unique()
    y_vals = filtered_df[y_col].dropna().unique()
    matrix = pd.DataFrame(index=sorted(y_vals), columns=sorted(x_vals), dtype=float)

    for x in x_vals:
        for y in y_vals:
            subset = filtered_df[(filtered_df[x_col] == x) & (filtered_df[y_col] == y)]
            if kpi_col in ["pickup_distance", "dropoff_distance"]:
                matrix.loc[y, x] = subset[kpi_col].median()
            else:
                matrix.loc[y, x] = _compute_kpi(subset, kpi_col, sla, cost_per_min)

    matrix.dropna(axis=0, how="all", inplace=True)
    matrix.dropna(axis=1, how="all", inplace=True)

    matrix = matrix.fillna(0)

    if y_col in label_mapper:
        matrix.index = matrix.index.map(label_mapper[y_col])
    if x_col in label_mapper:
        matrix.columns = matrix.columns.map(label_mapper[x_col])

    cap = np.nanpercentile(matrix.values, 95)
    matrix = np.clip(matrix, a_min=None, a_max=cap)

    fig, ax = plt.subplots(figsize=(10, 6))

    if kpi_col in ["total_orders", "pickup_distance", "dropoff_distance"]:
        cmap = "RdYlGn"  
    else:
        cmap = "RdYlGn_r"

    sns.heatmap(matrix, annot=True, fmt=".1f", cmap=cmap, ax=ax, annot_kws={"fontsize":6, "fontweight":"bold"})
    ax.set_title(f"{val_display} by {x_col} and {y_col}")
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    sns.set(font_scale=0.9)
    st.pyplot(fig)

def render_bubble_chart(df, x_kpi, y_kpi, size_enabled, size_kpi, category_col, filters):
    """
    Renderiza un diagrama de dispersión tipo bubble chart con dimensiones KPI.

    Parameters
    ----------
    df : pd.DataFrame
        Dataset sobre el cual se agruparán los KPIs.
    x_kpi : str
        KPI que se representa en el eje X.
    y_kpi : str
        KPI que se representa en el eje Y.
    size_enabled : bool
        Indica si el tamaño de los círculos se basa en un KPI o es fijo.
    size_kpi : str
        KPI a usar como tamaño si `size_enabled` es True.
    category_col : str
        Columna categórica usada para agrupar (y nombrar burbujas).
    filters : dict
        Diccionario con parámetros como SLA y costo por minuto.

    Returns
    -------
    None
        El gráfico se muestra en pantalla usando `st.plotly_chart`.
    """
    grouped = df.groupby(category_col).apply(
        lambda sub: pd.Series({
            k: _compute_kpi(sub, k, filters['sla'], filters['cost_per_min']) for k in [x_kpi, y_kpi, size_kpi] if k
        })
    ).reset_index()

    color_col = size_kpi
    
    if size_enabled and size_kpi:
        # Si el usuario ingresa un kpi para tamaño del marcador, lo usamos
        grouped = grouped.dropna(subset=[x_kpi, y_kpi, size_kpi])
        color_scale = "RdYlGn_r"
        final_size_col = size_kpi
    else:
        # Si no, ingresamos un valor genérico y usamos esa columna como tamaño
        grouped["Tamaño"] = 30

        # TO-DO esto no jala al 100, creo que tengo que cambiarlo directo en la configuración de plotly (?)
        grouped["Color"] = "Size was not enabled"
        final_size_col = "Tamaño"
        color_col = "Color"
        grouped = grouped.dropna(subset=[x_kpi, y_kpi])
    
    fig = px.scatter(
        grouped,
        x=x_kpi,
        y=y_kpi,
        size=final_size_col,
        color=color_col,
        hover_name=category_col,
        size_max=100,
        color_continuous_scale="RdYlGn_r",
        height=600
    )

    fig.add_trace(
        go.Scatter(
            x=grouped[x_kpi],
            y=grouped[y_kpi],
            mode="text",
            text=grouped[category_col],
            textposition="middle center",
            textfont=dict(
                size=11,
                color="black"
            ),
            showlegend=False,
            hoverinfo='skip'
        )
    )

    fig.update_layout(
        title=f"{y_kpi} vs {x_kpi} by {category_col}",
        xaxis_title=x_kpi,
        yaxis_title=y_kpi,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)

def render_driver_bar(filtered_df, filters, selected_kpi, rank_type):
    """
    Renderiza un gráfico de barras horizontal con los conductores mejor o peor rankeados.

    Parameters
    ----------
    filtered_df : pd.DataFrame
        Dataset filtrado que contiene entregas y predicciones.
    filters : dict
        Diccionario de filtros que incluye SLA y costo por minuto.
    selected_kpi : str
        Nombre del KPI a usar para el ranking.
    rank_type : str
        Tipo de ranking: 'Top 15' o 'Bottom 15'.

    Returns
    -------
    top_drivers : pd.DataFrame
        Subconjunto de los conductores seleccionados con sus KPIs.
    """
    driver_df = driver_kpis(filtered_df, sla=filters["sla"], cost_per_min=filters["cost_per_min"])

    kpi_min = driver_df[selected_kpi].min()
    kpi_max = driver_df[selected_kpi].max()
    
    ascending = selected_kpi in ["total_orders"] 

    ascending = not ascending if rank_type == "Top 15" else ascending

    top_drivers = driver_df.sort_values(by=selected_kpi, ascending=ascending).head(20)

    fig = px.bar(
        top_drivers,
        x=selected_kpi,
        y="driver_uuid",
        color=selected_kpi,
        orientation="h",
        text="driver_experience",
        hover_data= {
            "geo_archetype": True,
            "driver_experience": True,
            "median_ATD": ":.2f",
            "pct_breaches": ":.1f",
            "p95_ATD": ":.2f",
            "total_orders": ":,",
            "breach_cost": ":.0f",
            "over_under": ":.2f",
            selected_kpi: ":.2f"
        },
        color_continuous_scale="greens" if selected_kpi == "total_orders" else "RdYlGn_r",
        range_color=[kpi_min, kpi_max],
        height=600
    )

    fig.update_layout(
        title=f"{rank_type} Drivers by {selected_kpi}",
        xaxis_title=selected_kpi,
        yaxis_title="Driver UUID",
        yaxis=dict(autorange="reversed")
    )

    fig.update_traces(texttemplate="%{text}", textposition="outside")

    st.plotly_chart(fig, use_container_width=True)

    return top_drivers