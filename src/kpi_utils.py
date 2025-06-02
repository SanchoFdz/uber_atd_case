import numpy as np
import pandas as pd
import streamlit as st

@st.cache_data(show_spinner="Calculando KPIs...")
def calculate_kpis(df, df_prev, sla, cost_per_min):
    """
    Calcula indicadores clave de desempeño (KPIs) agregados, comparando periodo actual vs. previo.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame del periodo actual.
    df_prev : pd.DataFrame
        DataFrame del periodo previo para comparación.
    sla : float
        Umbral de SLA en minutos.
    cost_per_min : float
        Costo económico por minuto de incumplimiento.

    Returns
    -------
    kpis : list of tuples
        Lista con tuplas (nombre del KPI, valor actual, delta contra periodo previo, tipo de optimización).
    """
    kpis = []
    curr_median = df["ATD"].median()
    prev_median = df_prev["ATD"].median()

    kpis.append(("Median ATD", round(curr_median, 2), curr_median - prev_median, "reduce"))

    curr_breach = (df["ATD"] > sla).mean() * 100
    prev_breach = (df_prev["ATD"] > sla).mean() * 100
    kpis.append(("% Breaches", round(curr_breach, 2), curr_breach - prev_breach, "reduce"))

    kpis.append(("Total Orders", len(df), len(df) - len(df_prev), "increase"))

    curr_p95 = np.percentile(df["ATD"], 95)
    prev_p95 = np.percentile(df_prev["ATD"], 95)
    kpis.append(("P95 ATD", round(curr_p95, 2), curr_p95 - prev_p95, "reduce"))

    gamma = df['ATD'].quantile(0.999)
    lambda_param = 1
    breach_cost = ((df["ATD"] - sla).clip(0) * cost_per_min * ((1 + (df['ATD'] - sla).clip(0)/gamma)**lambda_param)).sum()
    prev_cost = ((df_prev["ATD"] - sla).clip(0) * cost_per_min * ((1 + (df_prev['ATD'] - sla).clip(0)/gamma)**lambda_param)).sum()
    kpis.append(("Total Breach Cost", round(breach_cost, 2), breach_cost - prev_cost, "reduce"))

    over_under = (df["ATD_pred"] - df["ATD"]).mean()
    prev_ou = (df_prev["ATD_pred"] - df_prev["ATD"]).mean()
    kpis.append(("Over/Under Pred", round(over_under, 2), over_under - prev_ou, "reduce"))

    return kpis

@st.cache_data(show_spinner="Calculando KPIs...")
def zone_kpis(df, sla, cost_per_min):
    """
    Calcula KPIs agregados por zona (territorio).

    Parameters
    ----------
    df : pd.DataFrame
        Dataset de entregas.
    sla : float
        Umbral de SLA.
    cost_per_min : float
        Costo por minuto de incumplimiento.

    Returns
    -------
    result : pd.DataFrame
        Tabla con métricas agregadas por territorio.
    """
    df = df.copy()

    gamma = df['ATD'].quantile(0.999)
    lambda_param = 1

    grouped = df.groupby("territory")

    result = grouped.agg(
        median_ATD=("ATD", "median"),
        p95_ATD=("ATD", lambda x: np.percentile(x, 95)),
        pct_breaches=("ATD", lambda x: (x > sla).mean() * 100),
        total_orders=("ATD", "count"),
        over_under=("ATD", lambda x: (df.loc[x.index, "ATD_pred"] - x).mean()),
        breach_cost=("ATD", lambda x: ((x - sla).clip(0) * cost_per_min * ((1 + ((x - sla).clip(0))/gamma)**lambda_param)).sum())
    ).reset_index()

    return result

@st.cache_data(show_spinner="Calculando KPIs...")
def _compute_kpi(df, kpi,sla,cost_per_min):
    """
    Calcula un KPI específico sobre un DataFrame dado.

    Parameters
    ----------
    df : pd.DataFrame
        Dataset sobre el que se calcula el KPI.
    kpi : str
        Nombre del KPI a calcular. Opciones:
        - "median_ATD"
        - "pct_breaches"
        - "total_orders"
        - "p95_ATD"
        - "breach_cost"
        - "over_under"
    sla : float
        Límite de tiempo (SLA).
    cost_per_min : float
        Costo por minuto fuera del SLA.

    Returns
    -------
    value : float
        Valor del KPI calculado.

    Raises
    ------
    ValueError
        Si el KPI especificado no está implementado.
    """

    if kpi == "median_ATD":
        return df["ATD"].median()

    if kpi == "pct_breaches":
        return (df["ATD"] > sla).mean() * 100

    if kpi == "total_orders":
        return len(df)

    if kpi == "p95_ATD":
        return np.nanpercentile(df["ATD"], 95)

    if kpi == "breach_cost":
        gamma = df["ATD"].quantile(0.999)
        lambda_param = 1
        return ((df["ATD"] - sla)
                .clip(lower=0)
                * cost_per_min
                * ((1 + (df["ATD"] - sla).clip(0) / gamma) ** lambda_param)
               ).sum()

    if kpi == "over_under":
        
        return (df["ATD_pred"] - df["ATD"]).mean()

    raise ValueError(f"KPI no reconocido: {kpi}")

@st.cache_data(show_spinner="Calculando KPIs...")
def trend_kpis(filtered_df, df_prev, kpi, sla, cost_per_min):
    """
    Genera series temporales suavizadas (rolling mean) para comparar la tendencia
    del KPI actual y el periodo anterior.

    Parameters
    ----------
    filtered_df : pd.DataFrame
        Datos actuales.
    df_prev : pd.DataFrame
        Datos del periodo anterior.
    kpi : str
        Nombre del KPI a calcular (ver `_compute_kpi`).
    sla : float
        SLA en minutos.
    cost_per_min : float
        Costo por minuto.

    Returns
    -------
    trend : pd.DataFrame
        DataFrame con columnas 'date', 'Current' y 'Previous' representando la serie temporal suavizada.
    """
    
    date_col = "date"
    window = 7

    daily_curr = (filtered_df
                  .groupby(date_col)
                  .apply(_compute_kpi, kpi, sla, cost_per_min)
                  .rename("Current"))

    daily_prev = (df_prev
                  .groupby(date_col)
                  .apply(_compute_kpi, kpi, sla, cost_per_min)
                  .rename("Previous"))

    curr_idx = pd.date_range(daily_curr.index.min(),
                             daily_curr.index.max(),
                             freq="D")
    
    prev_idx = pd.date_range(daily_prev.index.min(),
                             daily_prev.index.max(),
                             freq="D")

    daily_curr = daily_curr.reindex(curr_idx)
    daily_prev = daily_prev.reindex(prev_idx)

    curr_roll = daily_curr.rolling(window=window,
                                   min_periods=1).mean()

    prev_roll = daily_prev.rolling(window=window,
                                   min_periods=1).mean()

    offset = curr_idx[0] - prev_idx[0] 
    prev_roll.index = prev_roll.index + offset 

    trend = pd.concat([curr_roll, prev_roll], axis=1)
    trend = trend.reset_index(names="date")

    return trend

@st.cache_data(show_spinner="Calculando KPIs...")
def driver_kpis(df, sla, cost_per_min):
    """
    Calcula KPIs por conductor, incluyendo performance y caracterización geográfica.

    Parameters
    ----------
    df : pd.DataFrame
        Dataset con entregas y predicciones.
    sla : float
        Umbral máximo aceptable de ATD.
    cost_per_min : float
        Penalización económica por minuto de exceso.

    Returns
    -------
    result : pd.DataFrame
        Tabla agregada por `driver_uuid` con métricas clave y variables contextuales.
    """
    df = df.copy()

    df = df[df["driver_uuid"] != "Unassigned"].copy()

    df["over_under"] = df["ATD_pred"] - df["ATD"]
    df["delay"] = (df["ATD"] - sla).clip(lower=0)

    gamma = df["ATD"].quantile(0.999)
    lambda_param = 1
    df["breach_cost"] = (
        df["delay"] * cost_per_min * ((1 + df["delay"] / gamma) ** lambda_param)
    )

    def safe_mode(series):
        mode = series.mode()
        return mode.iloc[0] if not mode.empty else None

    grouped = df.groupby("driver_uuid")

    result = grouped.agg(
        median_ATD=("ATD", "median"),
        p95_ATD=("ATD", lambda x: np.percentile(x, 95)),
        pct_breaches=("ATD", lambda x: (x > sla).mean() * 100),
        total_orders=("ATD", "count"),
        over_under=("over_under", "mean"),
        breach_cost=("breach_cost", "sum"),
        geo_archetype=("geo_archetype", safe_mode),
        driver_experience=("driver_experience", safe_mode)
    ).reset_index()

    return result
