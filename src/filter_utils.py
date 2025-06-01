import numpy as np
import pandas as pd

def apply_filters(df, filters):
    """
    Aplica filtros sobre un DataFrame de entregas según criterios definidos y 
    extrae el periodo comparativo inmediatamente anterior para benchmarking.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame original con columnas como 'date', 'region', 'territory', etc.
    filters : dict
        Diccionario con los filtros seleccionados por el usuario. Debe contener:
            - "date_range": tuple de (start_date, end_date) tipo pd.Timestamp
            - "benchmark_length": int, número de días del periodo anterior
            - "region": list[str] o vacío
            - "territory": list[str] o vacío
            - "fleet": list[str] o vacío
            - "geo": list[str] o vacío
            - "driver_experience": list[str] o vacío
            - "hora_pico_ordenes": bool
            - "hora_pico_atd": bool
            - "weekend": bool

    Returns
    -------
    df_filtered : pd.DataFrame
        Subconjunto del DataFrame original filtrado según los criterios dados.
    df_prev : pd.DataFrame or None
        Subconjunto correspondiente al periodo anterior, con los mismos filtros.
        Si no hay datos suficientes, devuelve None.
    msg : str or None
        Mensaje de advertencia o error si no se puede generar el periodo comparativo,
        o None si todo salió bien.
    """
    df_filtered = df.copy()
    start, end = filters["date_range"]
    benchmark_days = filters["benchmark_length"]
    prev_start = start - pd.Timedelta(days=benchmark_days)
    prev_end = start - pd.Timedelta(days=1)

    try:
        # Filtrado por rango de fechas actual y periodo anterior
        df_filtered = df_filtered[(df_filtered["date"] >= start) & (df_filtered["date"] <= end)]
        df_prev = df[(df["date"] >= prev_start) & (df["date"] <= prev_end)]

        # Filtros categóricos
        for key, col in [("region", "region"), ("territory", "territory"),
                         ("fleet", "courier_flow"), ("geo", "geo_archetype"),
                         ("driver_experience", "driver_experience")]:
            if filters[key]:
                df_filtered = df_filtered[df_filtered[col].isin(filters[key])]
                df_prev = df_prev[df_prev[col].isin(filters[key])]

        # Filtros binarios
        if filters["hora_pico_ordenes"]:
            df_filtered = df_filtered[df_filtered["hora_pico_ordenes"] == 1]
            df_prev = df_prev[df_prev["hora_pico_ordenes"] == 1]

        if filters["hora_pico_atd"]:
            df_filtered = df_filtered[df_filtered["hora_pico_atd"] == 1]
            df_prev = df_prev[df_prev["hora_pico_atd"] == 1]

        if filters["weekend"]:
            df_filtered = df_filtered[df_filtered["is_weekend"] == 1]
            df_prev = df_prev[df_prev["is_weekend"] == 1]

        # Si el comparativo queda vacío, retornar advertencia
        if df_prev.empty:
            return df_filtered, None, "Not enough data from previous period for comparison."

        return df_filtered, df_prev, None

    except Exception as e:
        return df_filtered, None, f"Error applying filters: {e}"