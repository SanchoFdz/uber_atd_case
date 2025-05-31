import numpy as np
import pandas as pd

def apply_filters(df, filters):
    df_filtered = df.copy()
    start, end = filters["date_range"]
    benchmark_days = filters["benchmark_length"]
    prev_start = start - pd.Timedelta(days=benchmark_days)
    prev_end = start - pd.Timedelta(days=1)

    try:
        df_filtered = df_filtered[(df_filtered["date"] >= start) & (df_filtered["date"] <= end)]
        df_prev = df[(df["date"] >= prev_start) & (df["date"] <= prev_end)]

        for key, col in [("region", "region"), ("territory", "territory"),
                         ("fleet", "driver_category"), ("geo", "geo_archetype")]:
            if filters[key]:
                df_filtered = df_filtered[df_filtered[col].isin(filters[key])]
                df_prev = df_prev[df_prev[col].isin(filters[key])]

        if filters["peak_hour"]:
            df_filtered = df_filtered[df_filtered["peak_hour"]]
            df_prev = df_prev[df_prev["peak_hour"]]

        if filters["weekend"]:
            df_filtered = df_filtered[df_filtered["weekend"]]
            df_prev = df_prev[df_prev["weekend"]]

        if df_prev.empty:
            return df_filtered, None, "Not enough data from previous period for comparison."

        return df_filtered, df_prev, None
    except Exception as e:
        return df_filtered, None, f"Error applying filters: {e}"

def calculate_kpis(df, df_prev, sla, cost_per_min):
    df["yhat_test"] = 45
    df_prev["yhat_test"] = 45

    kpis = []
    curr_median = df["ATD"].median()
    prev_median = df_prev["ATD"].median()
    delta = 100 * (curr_median - prev_median) / prev_median
    kpis.append(("Median ATD", round(curr_median, 2), delta))

    curr_breach = (df["ATD"] > sla).mean() * 100
    prev_breach = (df_prev["ATD"] > sla).mean() * 100
    kpis.append(("% Breaches", round(curr_breach, 2), curr_breach - prev_breach))

    kpis.append(("Total Orders", len(df), len(df) - len(df_prev)))

    curr_p95 = np.percentile(df["ATD"], 95)
    prev_p95 = np.percentile(df_prev["ATD"], 95)
    kpis.append(("P95 ATD", round(curr_p95, 2), curr_p95 - prev_p95))

    breach_cost = ((df["ATD"] - sla).clip(0) * cost_per_min * np.exp(0.02 * (df["ATD"] - sla))).sum()
    prev_cost = ((df_prev["ATD"] - sla).clip(0) * cost_per_min * np.exp(0.02 * (df_prev["ATD"] - sla))).sum()
    kpis.append(("Total Breach Cost", round(breach_cost, 2), breach_cost - prev_cost))

    over_under = (df["yhat_test"] - df["ATD"]).mean()
    prev_ou = (df_prev["yhat_test"] - df_prev["ATD"]).mean()
    kpis.append(("Over/Under Pred", round(over_under, 2), over_under - prev_ou))

    return kpis

