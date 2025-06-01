import streamlit as st
import pandas as pd
import numpy as np
from src.global_filters import render_sidebar
from src.data_loader import build_historical_performance
from src.model_utils import simulate_plan

# Título de la sección principal de planeación y simulación
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
historical_perf, avg_orders_proxy = build_historical_performance(
    df,
    sla=filters["sla"],
    cost_per_min=filters["cost_per_min"]
)

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
    result = simulate_plan(sim_df, historical_perf, avg_orders_proxy)

    # Mostrar resultados formateados con dos decimales
    st.dataframe(result.style.format(precision=2))

    # Mensaje de éxito indicando que la simulación fue ejecutada
    st.success("Basic simulation based on historical performance")

else:
    # Mensaje informativo si no se ha cargado ningún archivo aún
    st.info("Upload a CSV to simulate your operations changes.")
