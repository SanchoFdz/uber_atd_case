import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from src.kpi_utils import apply_filters
import numpy as np
from src.global_filters import render_sidebar

st.title("🧠 Root Cause Analysis")

df = st.session_state.get("df")
filters = render_sidebar(df)

filtered_df, prev_df, error = apply_filters(df, filters)

if error:
    st.warning(error)
else:
    st.subheader("🔍 1. Heatmap Matrix")
    cols = filtered_df.columns.tolist()
    x_col = st.selectbox("X Axis", cols, index=cols.index("geo_archetype"))
    y_col = st.selectbox("Y Axis", cols, index=cols.index("driver_category"))
    val_col = st.selectbox("Value", ["ATD", "prep_time", "dropoff_distance"])

    heat_data = filtered_df.pivot_table(index=y_col, columns=x_col, values=val_col, aggfunc='mean')
    st.write(f"**Mean {val_col} by {x_col} and {y_col}**")
    fig, ax = plt.subplots()
    sns.heatmap(heat_data, annot=True, fmt=".1f", cmap="YlGnBu", ax=ax)
    st.pyplot(fig)

    st.subheader("🚴 2. Driver Performance Explorer")
    selected_kpi = st.selectbox("Rank by KPI", ["ATD", "dropoff_distance", "yhat_test"])
    agg = filtered_df.groupby("driver_uuid").agg({
        "ATD": "median",
        "dropoff_distance": "mean",
        "geo_archetype": lambda x: x.mode().iloc[0],
        "driver_category": lambda x: x.mode().iloc[0],
        "driver_orders": "sum",
        "yhat_test": "mean"
    }).reset_index()

    agg["experience"] = pd.cut(agg["driver_orders"], bins=[0, 10, 30, 100],
                               labels=["novice", "intermediate", "veteran"])

    top = agg.sort_values(by=selected_kpi, ascending=True).head(15)
    st.dataframe(top.style.format(precision=2))

    st.info("ℹ️ Hover tooltip logic is simulated using a data table. Full map/tooltip UI can be added via Plotly later.")

    st.subheader("🧩 3. More insights coming soon...")
    st.write("💡 Think about fleet distribution, hourly breakdowns, route patterns etc.")
