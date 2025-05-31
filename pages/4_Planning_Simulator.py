import streamlit as st
import pandas as pd
import numpy as np
from src.global_filters import render_sidebar

st.title("📋 Planning & Simulation")

df = st.session_state.get("df")
filters = render_sidebar(df)

st.markdown("Upload your **planning CSV** with `%driver_category`, `%fleet_mix`, and `drivers_per_day` for each region/day.")

uploaded = st.file_uploader("Upload Config CSV", type=["csv"])

if uploaded:
    sim_df = pd.read_csv(uploaded)
    st.write("📄 Uploaded Plan")
    st.dataframe(sim_df)

    st.subheader("📈 Simulated Impact")
    # Fake prediction logic (proxy)
    sim_df["Predicted Median ATD"] = 40 - sim_df["drivers_per_day"] * 0.2 + np.random.normal(0, 1, size=len(sim_df))
    sim_df["Predicted SLA Breach %"] = np.clip(100 - sim_df["drivers_per_day"] * 1.5, 0, 100)
    sim_df["Predicted Cost"] = sim_df["Predicted SLA Breach %"] * 1.5

    st.dataframe(sim_df.style.format(precision=2))
    st.success("🔮 Simulation complete! Model integration coming next.")
else:
    st.info("Upload a CSV to simulate your operations changes.")
