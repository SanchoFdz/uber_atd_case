import streamlit as st
import pandas as pd

def render_sidebar(df):
    # Only initialize once per session (per page load)
    if "filters" not in st.session_state:
        _initialize_filters(df)

    st.sidebar.image("./assets/uber_eats_logo.png", use_column_width=True)
    st.sidebar.header("Date Filters")

    min_date, max_date = df["date"].min(), df["date"].max()
    date_range = st.sidebar.date_input("Select date range", st.session_state.filters["date_range"])

    st.sidebar.header("Global Filters")
    sla = st.sidebar.slider("SLA threshold (minutes)", 10, 90, st.session_state.filters["sla"])
    cost_per_min = st.sidebar.slider("Cost per delayed minute", 1, 20, st.session_state.filters["cost_per_min"])
    region = st.sidebar.multiselect("Region", options=df["region"].unique(), default=st.session_state.filters["region"])
    territory = st.sidebar.multiselect("Territory", options=df["territory"].unique(), default=st.session_state.filters["territory"])
    fleet = st.sidebar.multiselect("Fleet type", options=df["courier_flow"].unique(), default=st.session_state.filters["fleet"])
    geo = st.sidebar.multiselect("Geo archetype", options=df["geo_archetype"].unique(), default=st.session_state.filters["geo"])
    weekend = st.sidebar.checkbox("Only Weekend", value=st.session_state.filters["weekend"])

    benchmark_length = (date_range[1] - date_range[0]).days

    st.session_state.filters = {
        "date_range": date_range,
        "benchmark_length": benchmark_length,
        "sla": sla,
        "cost_per_min": cost_per_min,
        "region": region,
        "territory": territory,
        "fleet": fleet,
        "geo": geo,
        "peak_hour": None,
        "weekend": weekend,
    }

    return st.session_state.filters


def _initialize_filters(df):
    min_date, max_date = df["date"].min(), df["date"].max()
    st.session_state.filters = {
        "date_range": [min_date, max_date],
        "benchmark_length": (max_date - min_date).days,
        "sla": 30,
        "cost_per_min": 5,
        "region": [],
        "territory": [],
        "fleet": [],
        "geo": [],
        "peak_hour": None,
        "weekend": False,
    }
