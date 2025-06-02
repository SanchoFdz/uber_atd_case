import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist

def simulate_plan_similarity(plan_df, historical_perf):
    """
    Estima los KPIs esperados para un plan operativo, comparando cada fila del plan
    contra observaciones históricas similares. La similitud se evalúa sobre una representación
    vectorial de la mezcla de experiencia y tipo de flota, junto con día y hora normalizados.

    Parameters
    ----------
    plan_df : pd.DataFrame
        Plan propuesto con columnas:
        - 'territory', 'day_of_week', 'hour', 'drivers_per_day'
        - '%<experience>' para cada tipo de experiencia
        - '%<flow>' para cada tipo de flota

    historical_perf : pd.DataFrame
        Observaciones históricas en formato largo, con columnas:
        - 'territory', 'day_of_week', 'hour'
        - 'driver_experience', 'courier_flow'
        - 'total_orders' y KPIs: 'median_ATD', 'p95_ATD', 'pct_breaches', 'breach_cost'

    Returns
    -------
    pd.DataFrame
        Simulación del desempeño esperado con columnas:
        - 'territory', 'day_of_week', 'hour', 'drivers_planned'
        - 'median_ATD', 'p95_ATD', 'pct_breaches', 'breach_cost', 'total_orders', 'expected_orders'
    """
    experiences = ['novice', 'low', 'medium', 'high', 'expert', 'unassigned']
    courier_flows = ['Fleet', 'Logistics', 'Motorbike', 'SUV', 'UberX', 'UberEats', 'Onboarder']

    results = []
    historical_perf = historical_perf.set_index(['territory', 'day_of_week', 'hour'], drop=False)

    for _, row in plan_df.iterrows():
        territory = row["territory"]
        day = row["day_of_week"]
        hour = row["hour"]
        n_drivers = row["drivers_per_day"] # Lo borré porque no me encanta lo que está saliendo

        # Vectorizacion del plan actual
        driver_mix_vector = np.array([row.get(f"%{exp}", 0.0) for exp in experiences])
        courier_mix_vector = np.array([row.get(f"%{flow}", 0.0) for flow in courier_flows])
        plan_vector = np.concatenate([[day], [hour], driver_mix_vector, courier_mix_vector])

        # tomamos los días y horas a +/- 2 y +/- 1 respectivamente de distancia
        # mod 7 porque así seguimos con la cintinuidad entre 0-6 y 0-23
        valid_days = [(day + i) % 7 for i in [-1, 0, 1]]
        valid_hours = [(hour + i) % 24 for i in range(-2, 3)]

        # Índices históricos que cumplen condiciones
        valid_idx = [
            idx for idx in historical_perf.index
            if idx[0] == territory and idx[1] in valid_days and idx[2] in valid_hours
        ] # Identificamos todas las filas del historico que coinciden con el territorio y +/- 1 día, +/- 2 horas

        if not valid_idx:
            continue

        vectors = []
        metric_info = []

        for idx in valid_idx:
            day_i, hour_i = idx[1], idx[2]
            
            hist_row = historical_perf.loc[idx]

            hist_drivers = row['drivers_per_day']

            hist_dm_vector = np.array([hist_row.get(f"%{exp}", 0.0) for exp in experiences])
            hist_courier_vector = np.array([hist_row.get(f"%{flow}", 0.0) for flow in courier_flows])
            hist_plan_vector = np.concatenate([[day_i], [hour_i], hist_dm_vector, hist_courier_vector])

            vectors.append(hist_plan_vector)
            
            metrics = historical_perf[
                (historical_perf["territory"] == territory) &
                (historical_perf["day_of_week"] == day_i) &
                (historical_perf["hour"] == hour_i)
            ].iloc[0]

            metric_info.append(metrics)

        vectors = np.vstack(vectors)
        distances = cdist([plan_vector], vectors, metric='euclidean')[0]
        sorted_indices = np.argsort(distances)

        k = min(5, len(sorted_indices))
        weights = 1 / (distances[sorted_indices[:k]] + 1e-5)
        weights /= weights.sum()

        selected_metrics = [metric_info[i] for i in sorted_indices[:k]]
        
        weighted_metrics = {
            "median_ATD": 0,
            "p95_ATD": 0,
            "pct_breaches": 0,
            "breach_cost": 0,
            "total_orders": 0
        }

        for i, metrics in enumerate(selected_metrics):
            for kpi in weighted_metrics:
                weighted_metrics[kpi] += metrics[kpi] * weights[i]

        for kpi in weighted_metrics:
            weighted_metrics[kpi] = round(weighted_metrics[kpi], 2)

        results.append({
            "territory": territory,
            "day_of_week": day,
            "hour": hour,
            "%novice": row['%novice'],
            "%low": row['%low'],
            "%medium": row['%medium'],
            "%high": row['%high'],
            "%expert": row['%expert'],
            "%unassigned": row['%unassigned'],
            "%Fleet": row['%Fleet'],
            "%Logistics": row['%Logistics'],
            "%Motorbike": row['%Motorbike'],
            "%Onboarder": row['%Onboarder'],
            "%SUV": row['%SUV'],
            "%UberEats": row['%UberEats'],
            "%UberX": row['%UberX'],
            #"drivers_planned": n_drivers,
            **weighted_metrics
        })

    return pd.DataFrame(results)