import streamlit as st
import pandas as pd
import datetime

def render_sidebar(df):
    """
    Renderiza la barra lateral en Streamlit para permitir al usuario configurar
    los filtros de análisis (rango de fechas, categorías, horas pico, etc.).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame con datos históricos, del cual se obtienen las opciones únicas
        para los filtros categóricos.

    Returns
    -------
    filters : dict
        Diccionario con todos los filtros configurados por el usuario, guardado en `st.session_state.filters`.
    """
    # Solo inicializar una vez por sesión
    if "filters" not in st.session_state:
        _initialize_filters(df)

    st.sidebar.image("./assets/uber_eats_logo.png", use_column_width=True)
    st.sidebar.header("Date Filters")

    min_date, max_date = df["date"].min(), df["date"].max()
    date_range = st.sidebar.date_input("Select date range", st.session_state.filters["date_range"])

    st.sidebar.header("Global Filters")
    sla = st.sidebar.slider("SLA threshold (minutes)", 10, 90, st.session_state.filters["sla"])
    cost_per_min = st.sidebar.slider("Cost per delayed minute (MXN)", 0.0, 3.0, value=float(st.session_state.filters["cost_per_min"]), step=0.1, format="%.2f")
    region = st.sidebar.multiselect("Region", options=df["region"].unique(), default=st.session_state.filters["region"])
    territory = st.sidebar.multiselect("Territory", options=df["territory"].unique(), default=st.session_state.filters["territory"])
    fleet = st.sidebar.multiselect("Courier type", options=df["courier_flow"].unique(), default=st.session_state.filters["fleet"])
    geo = st.sidebar.multiselect("Geo archetype", options=df["geo_archetype"].unique(), default=st.session_state.filters["geo"])
    weekend = st.sidebar.checkbox("Only Weekend", value=st.session_state.filters["weekend"])
    hora_pico_ordenes = st.sidebar.checkbox("Only Order Volume Peak Hour", value=st.session_state.filters["hora_pico_ordenes"])
    hora_pico_atd = st.sidebar.checkbox("Only ATD Peak Hour", value=st.session_state.filters["hora_pico_atd"])
    merchant_surface = st.sidebar.multiselect("Merchant surface", options=df["merchant_surface"].unique())
    driver_category = st.sidebar.multiselect("Driver experience", options=df["driver_experience"].unique(), default=st.session_state.filters["driver_experience"])

    # Exclusividad entre hora pico por órdenes y por ATD
    if hora_pico_ordenes:
        hora_pico_atd = False
    if hora_pico_atd:
        hora_pico_ordenes = False

    # Calcular días del benchmark
    if len(date_range) > 1:
        benchmark_length = (date_range[1] - date_range[0]).days + 1
    else:
        benchmark_length = 1
        date_range = [date_range[0], date_range[0]]

    apply = st.sidebar.button("Apply Filters")

    if apply:
        st.session_state.filters = {
            "date_range": date_range,
            "benchmark_length": benchmark_length,
            "sla": sla,
            "cost_per_min": cost_per_min,
            "region": region,
            "territory": territory,
            "fleet": fleet,
            "geo": geo,
            "merchant_surface": merchant_surface,
            "weekend": weekend,
            "hora_pico_ordenes": hora_pico_ordenes,
            "hora_pico_atd": hora_pico_atd,
            "driver_experience": driver_category
        }

    return st.session_state.filters


def _initialize_filters(df):
    """
    Inicializa los valores por defecto del diccionario de filtros en `st.session_state`
    si no existen ya. Toma como referencia la fecha máxima del DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame desde el cual se calcula la fecha de referencia para los filtros.

    Returns
    -------
    None
        Los filtros se guardan directamente en `st.session_state.filters`.
    """
    if "filters" in st.session_state:
        return  

    max_date = pd.to_datetime(df["date"].max()).date()

    st.session_state.filters = {
        "date_range": [max_date - pd.Timedelta(days=7), max_date],
        "benchmark_length": 7,
        "sla": 30,
        "cost_per_min": 5,
        "region": [],
        "territory": [],
        "fleet": [],
        "geo": [],
        'merchant_surface': [],
        "weekend": False,
        "hora_pico_ordenes": False,
        "hora_pico_atd": False,
        "driver_experience": []
    }
