import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


def compute_cost_and_emissions(distance_km: float, fuel_economy_kmpl: float, fuel_price_inr: float, co2_g_per_km: float):
    litres = distance_km / fuel_economy_kmpl
    cost_inr = litres * fuel_price_inr
    emissions_kg = (co2_g_per_km * distance_km) / 1000.0
    return round(cost_inr, 2), round(emissions_kg, 3)


def score_routes(routes_df: pd.DataFrame, weights: dict):
    """MinMax normalize [distance_km, duration_min, cost_inr, emissions_kg] then weighted sum.
    Returns sorted df and best index.
    """
    df = routes_df.copy()
    cols = ["distance_km", "duration_min", "cost_inr", "emissions_kg"]
    scaler = MinMaxScaler()
    norm = scaler.fit_transform(df[cols])
    norm_df = pd.DataFrame(norm, columns=[c + "_norm" for c in cols])
    w = np.array([weights.get(c, 1.0) for c in cols])
    df["score"] = (norm_df.values @ w.reshape(-1, 1)).flatten()
    best_idx = df["score"].idxmin()
    df["tag"] = ""
    df.loc[best_idx, "tag"] = "recommended"
    return df.sort_values(by="score").reset_index(drop=True), int(best_idx)
