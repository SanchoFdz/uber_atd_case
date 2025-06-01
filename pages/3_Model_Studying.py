import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import numpy as np
import os
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Título principal de la sección de exploración del modelo
st.title("📈 Model Performance Explorer")

# Definir ruta al archivo del modelo
base_dir = os.path.dirname(__file__)
model_path = os.path.join(base_dir, "../models/xgb_model.pkl")

# Recuperar datasets procesados desde el estado de sesión
df = st.session_state.get("df")        # Datos crudos con predicciones
df_prep = st.session_state.get("df_prep")  # Datos preprocesados (features de entrada)

# Subtítulo de la sección de métricas
st.subheader("📊 Model Metrics")

# Definir variables reales y predichas
y_true = df["ATD"]
y_pred = df["ATD_pred"]

# Transformaciones logarítmicas para métricas sensibles a escalas
y_pred_log = np.log1p(y_pred)
y_true_log = np.log1p(y_true)

# Calcular métricas de evaluación del modelo
mae = mean_absolute_error(y_true, y_pred)         # Error absoluto medio
rmse = np.sqrt(mean_squared_error(y_true, y_pred))# Raíz del error cuadrático medio
r2 = r2_score(y_true_log, y_pred_log)             # R² sobre espacio logarítmico

# Mostrar métricas en formato visual de 3 columnas
col1, col2, col3 = st.columns(3)
col1.metric("MAE", f"{mae:.2f}")
col2.metric("RMSE", f"{rmse:.2f}")
col3.metric("R²", f"{r2:.2f}")

# Subtítulo de la sección de importancia de variables
st.subheader("🔍 Feature Importances from model")

# Explicación expandible sobre qué significa la importancia de variables
with st.expander("📘 What is Feature Importance?"):
    st.markdown("""
    **Feature Importance** tells us which features (inputs) the model relied on the most to make predictions.  
    For example, in predicting *ATD (actual time to delivery)*:

    - `pickup_distance` had the **strongest impact** — longer pickups often mean longer deliveries.
    - Time-based features (like `hour` or `day_of_week`) also played a key role.
    - Features like territory or courier platform give **insight into operational bottlenecks**.

    This is **important** because it helps us understand what factors most influence delivery times, allowing us to focus on improving those areas.
    """)

# Cargar modelo entrenado desde archivo
model = joblib.load(model_path)

# Extraer importancias de variables desde el modelo (por tipo "gain")
importances = model.feature_importances_

# Permitir al usuario elegir cuántas variables mostrar
max_feats = st.slider(
    "🔢 Number of Top Features to Display",
    min_value=5,
    max_value=50,
    value=15
)

# Crear figura de importancias
fig, ax = plt.subplots(figsize=(10, 6))

# Usar herramienta integrada de XGBoost para graficar importancias
xgb.plot_importance(
    model,
    max_num_features=max_feats,
    importance_type="gain",
    ax=ax
)

# Título del gráfico
ax.set_title(f"Top {max_feats} Feature Importances from XGBoost")

# Mostrar el gráfico en la interfaz de Streamlit
st.pyplot(fig)
