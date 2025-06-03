import streamlit as st
import pandas as pd

# Título de la sección principal del explorador de datos
st.title("🧾 Raw Data Explorer")

# Obtener DataFrame desde el estado de sesión y asegurarse de trabajar sobre una copia
df = st.session_state.get("df").copy()
df["date"] = pd.to_datetime(df["date"])  # Asegurar que la columna de fechas sea tipo datetime

# Instrucción para el usuario
st.markdown("Use filters below to narrow down your data by **multiple columns** 👇")

# Panel expandible que contiene todos los filtros
with st.expander("🔍 Filter Options", expanded=True):
    selected_filters = {}
    columns = df.columns.tolist()
    filter_base_df = df.copy()  # Se mantiene una copia para referencia

    # --- Filtro de rango de fechas ---
    min_date, max_date = df["date"].min().date(), df["date"].max().date()
    date_range = st.date_input("Filter by Date Range", [min_date, max_date], key="filter_date")
    start_date = pd.Timestamp(date_range[0])
    end_date = pd.Timestamp(date_range[1])
    selected_filters["date"] = (start_date, end_date)

    # --- Filtro por hora, si existe ---
    if "hour" in df.columns:
        hour_min, hour_max = int(df["hour"].min()), int(df["hour"].max())
        hour_range = st.slider("Filter by Hour", hour_min, hour_max, (hour_min, hour_max), key="filter_hour")
        selected_filters["hour"] = hour_range

    # --- Filtros multiselect por columna categórica ---
    for col in df.columns:
        if col in ["date", "hour"]:
            continue  # Ya están filtrados por separado

        unique_vals = filter_base_df[col].dropna().unique()
        if len(unique_vals) < 30:  # Sólo si la cardinalidad es baja
            selected_vals = st.multiselect(f"{col}", sorted(unique_vals), default=[], key=f"filter_{col}")
            if selected_vals:
                selected_filters[col] = selected_vals

    # --- Filtros para SLA y penalización ---
    st.markdown("---")
    st.markdown("### ⚙️ SLA & Delay Cost Filters")
    sla = st.slider("Select SLA threshold (minutes)", 5, 90, 30)
    cost_per_min = st.slider("Cost per delayed minute", min_value=0.0, max_value=3.0, value=0.1, step=0.1)

# === Aplicar los filtros seleccionados ===
df_filtered = df.copy()

# Filtro por fecha
if "date" in selected_filters:
    start, end = selected_filters["date"]
    df_filtered = df_filtered[(df_filtered["date"] >= start) & (df_filtered["date"] <= end)]

# Filtro por hora
if "hour" in selected_filters:
    h_start, h_end = selected_filters["hour"]
    df_filtered = df_filtered[df_filtered["hour"].between(h_start, h_end)]

# Filtros multiselect restantes
for col, vals in selected_filters.items():
    if col in ["date", "hour"]:
        continue
    df_filtered = df_filtered[df_filtered[col].isin(vals)]

# --- Cálculo de KPIs derivados ---
df_filtered["delay_minutes"] = (df_filtered["ATD"] - sla).clip(lower=0)  # Retrasos positivos solamente
gamma = df_filtered['ATD'].quantile(0.99)
lambda_param = 1

df_filtered['breach_cost'] = (df_filtered['ATD'] - sla).clip(0) * cost_per_min * ((1 + ((df_filtered['ATD'] - sla).clip(0))/gamma)**lambda_param)

# === Mostrar resultados ===
st.subheader("📄 Filtered Data")
st.markdown(f"Showing **{len(df_filtered):,}** rows with active filters.")

# Vista previa de hasta 500 filas
st.dataframe(df_filtered.head(500), use_container_width=True)

# --- Botón de descarga ---
csv = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button("⬇️ Download CSV", data=csv, file_name="filtered_data.csv")

