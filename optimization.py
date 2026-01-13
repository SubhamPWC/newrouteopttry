import numpy as np
import pandas as pd

# Pure calculators

def compute_cost_and_emissions(distance_km: float, fuel_economy_kmpl: float, fuel_price_inr: float, co2_g_per_km: float):
    litres = max(distance_km, 0.0) / max(fuel_economy_kmpl, 0.0001)
    cost_inr = litres * fuel_price_inr
    emissions_kg = (co2_g_per_km * max(distance_km, 0.0)) / 1000.0
    return round(cost_inr, 2), round(emissions_kg, 3)

# We set score to 0 for all rows and pick recommended by minimum time

def tag_and_zero_score(df: pd.DataFrame):
    if df.empty:
        df["score"] = []
        return df, -1
    best_idx = int(df["duration_min"].idxmin())
    df["score"] = 0.0
    df["tag"] = ""
    df.loc[best_idx, "tag"] = "recommended"
    return df.sort_values(by=["tag"], ascending=False).reset_index(drop=True), best_idx
