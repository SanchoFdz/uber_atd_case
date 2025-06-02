import streamlit as st
import pandas as pd
import numpy as np
from src.global_filters import render_sidebar
from src.data_loader import build_historical_performance
from src.model_utils import simulate_plan_similarity
import os

# Título de la sección principal de planeación y simulación
base_dir = os.path.dirname(__file__)
st.title("📋 Planning & Simulation")

# Cargar el DataFrame principal desde el estado de sesión
df = st.session_state.get("df")

# Mostrar barra lateral de filtros para limitar el contexto de la simulación
filters = render_sidebar(df)

# Instrucción textual sobre el formato esperado del archivo a subir
st.markdown(
    "Upload your **planning CSV** with `%driver_category`, `%fleet_mix`, "
    "and `drivers_per_day` for each region/day."
)

# Componente para subir archivo CSV con la planeación del usuario
uploaded = st.file_uploader("Upload Config CSV", type=["csv"])

# Calcular performance histórico para simular impacto de cambios propuestos
hist_long_path = os.path.join(base_dir, "../data/processed/historical_performance_long.parquet")

if not os.path.exists(hist_long_path):
    hist_long_df = build_historical_performance(df, filters['sla'], filters['cost_per_min'], hist_long_path)
    st.session_state.hist_long_df = hist_long_df
else:
    hist_long_df = pd.read_parquet(hist_long_path)
    st.session_state.hist_long_df = hist_long_df

# Si el usuario sube un archivo de configuración
if uploaded:
    # Leer el archivo subido como DataFrame
    sim_df = pd.read_csv(uploaded)

    # Mostrar el plan cargado
    st.write("📄 Uploaded Plan")
    st.dataframe(sim_df)

    # Subtítulo para la sección de resultados de simulación
    st.subheader("📈 Simulated Impact")

    # Ejecutar simulación del plan con base en datos históricos
    result = simulate_plan_similarity(sim_df, hist_long_df)

    # Mostrar resultados formateados con dos decimales
    st.dataframe(result)

    # Mensaje de éxito indicando que la simulación fue ejecutada
    st.success("Basic simulation based on historical performance")

else:
    # Mensaje informativo si no se ha cargado ningún archivo aún
    st.info("Upload a CSV to simulate your operations changes.")
