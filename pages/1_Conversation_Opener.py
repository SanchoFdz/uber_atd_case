# 1_Conversation_Opener.py
import streamlit as st
import numpy as np
from src.kpi_utils import calculate_kpis, apply_filters
from src.global_filters import render_sidebar
from src.style_utils import format_number

df = st.session_state.get("df")
filters = render_sidebar(df)

st.title("📊 Conversation Openers")

filters = st.session_state.get("filters", {})

if not filters:
    st.warning("Please set filters in the sidebar.")
else:
    filtered_df, prev_df, error = apply_filters(df, filters)

    if error:
        st.warning(error)
    else:
        kpis = calculate_kpis(filtered_df, prev_df, filters["sla"], filters["cost_per_min"])

        for i in range(0, len(kpis), 3):
            cols = st.columns(3)
            for j, (title, value, delta) in enumerate(kpis[i:i+3]):
                with cols[j]:
                    prev_val = value - delta
                    color = "green" if delta >= 0 else "red"

                    # Smart formatting
                    formatted_value = format_number(value, is_currency="Cost" in title)
                    formatted_prev = format_number(prev_val, is_currency="Cost" in title)

                    # Display nicely
                    st.markdown(f"""
                    <div class="kpi-card">
                        <h5 style="text-align:center;">{title}</h5>
                        <h2 style="text-align:center;">{formatted_value}</h2>
                        <p style="text-align:center; font-size:0.8em; color:{color};">
                            Prev: {formatted_prev} ({delta:+.1f}%)
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

        st.subheader("🗺️ KPI Heatmap over Mexico City")
        st.map(filtered_df[['dropoff_distance', 'pickup_distance']].rename(columns={
            'dropoff_distance': 'lat', 'pickup_distance': 'lon'
        }).sample(min(100, len(filtered_df))))

        st.subheader("📈 Rolling KPI Trends")
        if filters["benchmark_length"] < 7:
            st.info("Please select at least 7 days to view rolling trends.")
        else:
            trend_kpi = st.selectbox("Select KPI", ["Median ATD", "% SLA Breaches", "P95 ATD"])
            df_trend = filtered_df.groupby("date").agg({
                "ATD": ["median", lambda x: np.percentile(x, 95)],
            }).droplevel(1, axis=1).rename(columns={"median": "Median ATD", "<lambda_0>": "P95 ATD"})

            df_trend["% SLA Breaches"] = filtered_df.groupby("date").apply(
                lambda x: (x["ATD"] > filters["sla"]).mean() * 100
            )
            st.line_chart(df_trend[trend_kpi].rolling(7).mean())

