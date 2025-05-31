import streamlit as st
import pandas as pd
from src.global_filters import render_sidebar

df = st.session_state.get("df")
filters = render_sidebar(df)

st.title("🧾 Raw Data Explorer")

df = st.session_state.get("df")

st.subheader("🔍 Filter")
columns = df.columns.tolist()
filter_col = st.selectbox("Select column to filter", columns)
unique_vals = df[filter_col].dropna().unique().tolist()
selected_vals = st.multiselect("Select values", unique_vals, default=unique_vals[:3])

df_filtered = df[df[filter_col].isin(selected_vals)]

st.subheader("📄 Filtered Data")
st.dataframe(df_filtered.head(500))

csv = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button("⬇️ Download CSV", data=csv, file_name="filtered_data.csv")
