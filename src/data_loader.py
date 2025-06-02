import pandas as pd
import streamlit as st
import numpy as np
import os
import datetime
import json
import geopandas as gpd
import joblib


@st.cache_data
def load_data():
    """
    Carga los datos del dashboard, incluyendo predicciones del modelo si no están presentes.

    Parameters
    ----------
    None

    Returns
    -------
    df : pd.DataFrame
        DataFrame crudo con variables originales y predicción ATD.
    df_prep : pd.DataFrame
        DataFrame preparado con variables listas para modelado.
    """

    base_dir = os.path.dirname(__file__)  # Obtiene el directorio base del archivo actual

    data_path = os.path.join(base_dir, "../data/views/vw_ATD_dashboard.parquet")
    model_path = os.path.join(base_dir, "../models/xgb_model.pkl")
    views_dir = os.path.join(base_dir, "../data/views")

    if not os.path.exists(views_dir):
        os.makedirs(views_dir)

    if os.path.exists(data_path):  # Si el archivo de datos ya existe, lo carga
        df = pd.read_parquet(data_path)
    else:
        # Si no existe, genera los datos desde cero
        df = prepare_data(base_dir)
        df = driver_experience_bins(df, base_dir)

        # Guarda el resultado para evitar tener que repetir el proceso
        save_path = os.path.join(base_dir, "../data/views/vw_ATD_dashboard.parquet")
        df.to_parquet(save_path, index=False)

    # Si aún no se han hecho predicciones, se aplica el modelo
    if "ATD_pred" not in df.columns:
        model = joblib.load(model_path)

        df_prep = feature_selection(df)
        target = 'ATD_log'
        X = df_prep.drop(columns=[target]).copy()

        # Predicción del modelo en log-space
        df["ATD_log_pred"] = model.predict(X)
        df["ATD_pred"] = np.expm1(df["ATD_log_pred"])  # Se revierte el log

        # Guarda el dataset con predicciones
        df.to_parquet(data_path, index=False)
    else:
        df_prep = feature_selection(df)  # Si ya hay predicciones, solo genera features

    return df, df_prep


def feature_selection(df_view):
    """
    Aplica ingeniería de features sobre el DataFrame crudo para modelado.

    Parameters
    ----------
    df_view : pd.DataFrame
        DataFrame original con columnas sin procesar.

    Returns
    -------
    df_prep : pd.DataFrame
        DataFrame transformado y con variables dummy listo para modelado.
    """
    df = df_view.copy()
    
    # Crear variable target en espacio logarítmico
    df['ATD_log'] = np.log1p(df['ATD'].fillna(0))
    
    # Crear feature que indica si falta la hora de ofrecimiento
    if "restaurant_offered_timestamp_local" in df.columns:
        df["rest_offer_missing"] = df["restaurant_offered_timestamp_local"].isna().astype(int)

    # Imputación y flags de NaNs para distancias
    for col in ["pickup_distance", "dropoff_distance"]:
        nan_flag = f"{col}_nan"
        df[nan_flag] = df[col].isna().astype(int)
        
        # Imputación por media condicional
        df[col] = df.groupby(["territory", "day_of_week", "hour"])[col].transform(lambda s: s.fillna(s.mean()))
        
        # Si quedan NaNs, imputar con la mediana general
        df[col].fillna(df[col].median(), inplace=True)

    # Features de hora (cíclicos)
    df["sin_hour"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["cos_hour"] = np.cos(2 * np.pi * df["hour"] / 24)

    # Transformaciones logarítmicas
    for col in ["pickup_distance", "dropoff_distance"]:
        df[f"{col}_log"] = np.log1p(df[col])

    # Ratio entre pickup y dropoff (protegiendo contra div/0 o NaNs)
    df["pickup_dropoff_ratio"] = (
        df["pickup_distance_log"] / df["dropoff_distance_log"]
    ).replace([np.nan, np.inf, -np.inf], 1)

    # Variables dummies
    df = pd.get_dummies(df, columns=["courier_flow"], prefix="courier", drop_first=True)
    df = pd.get_dummies(df, columns=["geo_archetype"], prefix="geo", drop_first=True)
    df = pd.get_dummies(df, columns=["merchant_surface"], prefix="surface", drop_first=True)
    df = pd.get_dummies(df, columns=["region"], prefix="region", drop_first=True)
    df = pd.get_dummies(df, columns=["territory"], prefix="territory", drop_first=True)

    # Winsorización del ratio y log
    df['pickup_dropoff_ratio_winsor_log'] = np.log1p(df['pickup_dropoff_ratio'].clip(
        lower=df['pickup_dropoff_ratio'].quantile(0.01),
        upper=df['pickup_dropoff_ratio'].quantile(0.99)
    ))

    # Eliminar columnas que no deben ir al modelo
    drops = ['country_name', 'workflow_uuid', 'driver_uuid', 'delivery_trip_uuid',
        'restaurant_offered_timestamp_utc', 'order_final_state_timestamp_local',
        'eater_request_timestamp_local', 'pickup_distance', 'dropoff_distance',
        'ATD', 'restaurant_offered_timestamp_local', 'date', 'ATD_winsor',
        'dropoff_distance_nan', 'pickup_dropoff_ratio',
        'pickup_dropoff_ratio_log', 'pickup_dropoff_ratio_winsor']

    df_prep = df.drop(columns=drops, inplace=False, errors='ignore')

    # Variables categóricas adicionales
    df_prep = pd.get_dummies(df_prep, columns=["hour_bin", "driver_experience"], drop_first=True)

    return df_prep

@st.cache_data(show_spinner="Calculando KPIs...")
def load_gdf():
    """
    Carga un GeoDataFrame con datos geográficos procesados.

    Parameters
    ----------
    None

    Returns
    -------
    gdf : gpd.GeoDataFrame
        GeoDataFrame con información territorial o espacial.
    """
    base_dir = os.path.dirname(__file__)
    data_path = os.path.join(base_dir,"../data/processed/mun21gw.parquet")

    # Carga el GeoDataFrame con información geoespacial
    gdf = gpd.read_parquet(data_path)

    return gdf

def prepare_data(base_dir):
    """
    Carga, limpia y transforma el dataset crudo desde CSV a DataFrame estructurado.

    Parameters
    ----------
    base_dir : str
        Ruta base donde se encuentran los archivos.

    Returns
    -------
    df : pd.DataFrame
        DataFrame con columnas limpias, convertidas, e iniciales de análisis.
    """
    data_path = os.path.join(base_dir, "../data/raw/BC_A&A_with_ATD.csv")
    df = pd.read_csv(data_path)

    # Parseo de timestamps
    timestamp_cols = [
        'restaurant_offered_timestamp_utc',
        'order_final_state_timestamp_local',
        'eater_request_timestamp_local'
    ]
    for col in timestamp_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    # Conversión de zonas horarias
    df['restaurant_offered_timestamp_local'] = df['restaurant_offered_timestamp_utc'].dt.tz_localize('UTC').dt.tz_convert('America/Mexico_City')
    df['eater_request_timestamp_local'] = df['eater_request_timestamp_local'].dt.tz_localize('America/Mexico_City')
    df['order_final_state_timestamp_local'] = df['order_final_state_timestamp_local'].dt.tz_localize('America/Mexico_City')

    # Casting y limpieza
    categorical_cols = ['region', 'territory', 'country_name', 'courier_flow', 'geo_archetype', 'merchant_surface']
    df["courier_flow"].fillna("Unknown", inplace=True)
    df[categorical_cols] = df[categorical_cols].astype('category')

    uuid_cols = ['workflow_uuid', 'driver_uuid', 'delivery_trip_uuid']
    df[uuid_cols] = df[uuid_cols].astype(str)

    numeric_cols = ['pickup_distance', 'dropoff_distance']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    df.replace('\\N', np.nan, inplace=True)

    # Nuevas variables de fecha/hora
    df['date'] = df['eater_request_timestamp_local'].dt.date
    df['hour'] = df['eater_request_timestamp_local'].dt.hour
    df['day_of_week'] = df['eater_request_timestamp_local'].dt.day_of_week
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

    # Limpieza de UUIDs vacíos
    df["driver_uuid"].fillna("Unassigned", inplace=True)

    # Limpieza de categorías
    df['geo_archetype'] = df['geo_archetype'].replace('Defend CP', 'Defend_CP')

    # Cálculo de hora pico por número de órdenes y por ATD
    ordenes_por_hora = df.groupby('hour')['ATD'].size()
    hora_pico_ordenes = ordenes_por_hora.idxmax()    
    inicio_hpo = (hora_pico_ordenes - 2) % 24
    fin_hpo = (hora_pico_ordenes + 2) % 24

    atd_por_hora = df.groupby('hour')['ATD'].mean()
    hora_pico_atd = atd_por_hora.idxmax()    
    inicio_hpa = (hora_pico_atd - 2) % 24
    fin_hpa = (hora_pico_atd + 2) % 24

    df['hora_pico_ordenes'] = df['hour'].between(inicio_hpo, fin_hpo).astype(int)
    df['hora_pico_atd'] = df['hour'].between(inicio_hpa, fin_hpa).astype(int)
    
    df['hour_bin'] = df['hour'].apply(bin_hours)

    return df

def bin_hours(hour):
    """
    Agrupa horas en bins de 4 horas para análisis de series temporales.

    Parameters
    ----------
    hour : int
        Hora en formato entero (0-23).

    Returns
    -------
    str
        String representando el bin de hora correspondiente (ej. '08-12').
    """
    # Agrupa las horas en bloques de 4
    if hour < 4:
        return '00-04'
    elif hour < 8:
        return '04-08'
    elif hour < 12:
        return '08-12'
    elif hour < 16:
        return '12-16'
    elif hour < 20:
        return '16-20'
    else:
        return '20-24'
    
import pandas as pd
import os

def driver_experience_bins(df, base_dir, save_path="../data/views/driver_experience.parquet"):
    """
    Crea categorías de experiencia del conductor según número de órdenes históricas
    y las agrega al DataFrame original. También actualiza snapshot persistente.

    Parameters
    ----------
    df : pd.DataFrame
        Dataset con columna `driver_uuid` y `date`.
    base_dir : str
        Ruta base para resolver el path al archivo parquet.
    save_path : str, optional
        Ruta relativa al archivo de snapshot de experiencia (por defecto está predefinido).

    Returns
    -------
    df_copy : pd.DataFrame
        Mismo DataFrame con nueva columna `driver_experience`.
    """
    save_path = os.path.join(base_dir, save_path)
    df_copy = df.copy()

    # Filtrar conductores asignados y contar órdenes
    assigned_mask = df_copy["driver_uuid"] != "Unassigned"
    driver_counts = df_copy.loc[assigned_mask, "driver_uuid"].value_counts().reset_index()
    driver_counts.columns = ["driver_uuid", "total_orders"]

    # Definir bins de experiencia
    bins = [0, 4, 8, 15, 30, float('inf')]
    labels = ["novice", "low", "medium", "high", "expert"]

    driver_counts["driver_experience"] = pd.cut(driver_counts["total_orders"], bins=bins, labels=labels)

    # Crear snapshot temporal para seguimiento
    snapshot_date = pd.to_datetime(df_copy["date"].max())
    driver_counts["snapshot_week"] = snapshot_date.isocalendar().week
    driver_counts["snapshot_year"] = snapshot_date.isocalendar().year
    driver_counts['meta_created'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Unir con histórico si existe
    if os.path.exists(save_path):
        old_snapshots = pd.read_parquet(save_path)
        combined = pd.concat([old_snapshots, driver_counts], ignore_index=True)
        combined = combined.drop_duplicates(
            subset=["driver_uuid", "snapshot_week", "snapshot_year"],
            keep="last"
        )
    else:
        combined = driver_counts

    combined.to_parquet(save_path, index=False)

    # Merge con dataset original
    df_copy = df_copy.merge(
        driver_counts[["driver_uuid", "driver_experience"]],
        on="driver_uuid",
        how="left"
    )

    df_copy["driver_experience"] = (
        df_copy["driver_experience"]
        .astype("category")
        .cat.add_categories("unassigned")
        .fillna("unassigned")
    )

    return df_copy

st.cache_data()
def build_historical_performance(df, sla, cost_per_min):
    """
    Agrega métricas históricas de performance a nivel de grupo (driver exp + zona + hora + día + fleet).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame procesado que incluye `ATD`, `driver_experience`, `territory`, etc.
    sla : float
        Límite de SLA en minutos para calcular incumplimientos.
    cost_per_min : float
        Costo económico asociado a cada minuto de incumplimiento.

    Returns
    -------
    performance : pd.DataFrame
        Tabla agregada con métricas como mediana, p95, porcentaje de incumplimiento y costos.
    avg_orders_per_driver : pd.DataFrame
        Tabla con promedio de órdenes por driver en cada grupo.
    """
    df = df[df["driver_experience"] != "unassigned"].copy()

    # Cálculo del promedio de órdenes por repartidor
    orders_by_driver = (
        df.groupby(["territory", "day_of_week", "hour", "driver_uuid"])
          .size()
          .reset_index(name="orders_per_driver")
    )

    avg_orders_per_driver = (
        orders_by_driver.groupby(["territory", "day_of_week", "hour"])
        .agg(mean_orders_per_driver=("orders_per_driver", "mean"))
        .reset_index()
    )

    # Marca si una orden incumple SLA
    df["breach"] = (df["ATD"] > sla).astype(int)

    gamma = df['ATD'].quantile(0.999)  # Umbral extremo para penalización
    lambda_param = 1

    grouped = df.groupby(["territory", "day_of_week", "hour", "driver_experience", "courier_flow"])

    performance = grouped.agg(
        median_ATD=("ATD", "median"),
        p95_ATD=("ATD", lambda x: np.percentile(x, 95)),
        pct_breaches=("breach", "mean"),
        total_orders=("ATD", "count"),
        breach_cost=("ATD", lambda x: ((x - sla).clip(0) * cost_per_min * ((1 + ((x - sla).clip(0))/gamma)**lambda_param)).sum())
    ).reset_index()

    return performance, avg_orders_per_driver

    