import pandas as pd
import numpy as np

def simulate_plan(plan_df, historical_perf, avg_orders_proxy):
    """
    Simula el desempeño esperado de un plan operativo de asignación de conductores,
    utilizando datos históricos de desempeño por tipo de repartidor y tipo de flota.

    Para cada fila del plan (territorio + día + hora + mezcla de conductores y flota),
    calcula los KPIs esperados ponderando las métricas históricas por el mix propuesto.

    Parameters
    ----------
    plan_df : pd.DataFrame
        DataFrame con el plan de operación, debe incluir columnas:
        - 'territory', 'day_of_week', 'hour', 'drivers_per_day'
        - '%novice', '%low', ..., '%expert'
        - '%<courier_flow>' para cada tipo relevante de flota.

    historical_perf : pd.DataFrame
        DataFrame histórico con métricas de desempeño agregadas por combinación de:
        - 'territory', 'day_of_week', 'hour', 'driver_experience', 'courier_flow'
        y columnas como: 'median_ATD', 'p95_ATD', 'pct_breaches', 'breach_cost', 'total_orders'.

    avg_orders_proxy : pd.DataFrame
        DataFrame con la métrica `mean_orders_per_driver` por combinación de:
        - 'territory', 'day_of_week', 'hour'

    Returns
    -------
    pd.DataFrame
        Simulación del desempeño esperado, con columnas:
        - 'territory', 'day_of_week', 'hour', 'drivers_planned'
        - 'median_ATD', 'p95_ATD', 'pct_breaches', 'breach_cost', 'total_orders', 'expected_orders'
    """
    results = []

    for _, row in plan_df.iterrows():
        territory = row["territory"]
        day = row["day_of_week"]
        hour = row["hour"]
        n_drivers = row["drivers_per_day"]

        # Mezcla de experiencia
        driver_mix = {
            "novice": row["%novice"],
            "low": row["%low"],
            "medium": row["%medium"],
            "high": row["%high"],
            "expert": row["%expert"],
        }

        # Mezcla de flota (courier_flow)
        courier_mix = {
            k.replace("%", ""): v for k, v in row.items()
            if "%" in k and k.replace("%", "") in historical_perf["courier_flow"].unique()
        }

        total_weight = 0

        # Inicializar acumuladores ponderados
        weighted_metrics = {
            "median_ATD": 0,
            "p95_ATD": 0,
            "pct_breaches": 0,
            "breach_cost": 0,
            "total_orders": 0
        }

        # Ponderar métricas por mezcla de experiencia y tipo de flota
        for exp, exp_pct in driver_mix.items():
            for flow, flow_pct in courier_mix.items():
                weight = exp_pct * flow_pct
                total_weight += weight

                match = historical_perf[
                    (historical_perf["territory"] == territory) &
                    (historical_perf["day_of_week"] == day) &
                    (historical_perf["hour"] == hour) &
                    (historical_perf["driver_experience"] == exp) &
                    (historical_perf["courier_flow"] == flow)
                ]

                if not match.empty:
                    row_perf = match.iloc[0]
                    for k in weighted_metrics:
                        weighted_metrics[k] += row_perf[k] * weight

        # Estimar órdenes esperadas con proxy histórico
        match_proxy = avg_orders_proxy[
            (avg_orders_proxy["territory"] == territory) &
            (avg_orders_proxy["day_of_week"] == day) &
            (avg_orders_proxy["hour"] == hour)
        ]

        avg_orders = match_proxy["mean_orders_per_driver"].values
        expected_orders = n_drivers * avg_orders[0] if len(avg_orders) > 0 else np.nan
        weighted_metrics["expected_orders"] = expected_orders

        results.append({
            "territory": territory,
            "day_of_week": day,
            "hour": hour,
            "drivers_planned": n_drivers,
            **weighted_metrics
        })

    return pd.DataFrame(results)
