import streamlit as st
import pandas as pd

from optimization import compute_cost_and_emissions, score_routes
from map_utils import draw_routes_map
from multimodal import ORSClient

DEFAULTS = {
    "fuel_price_inr_per_litre": 110.0,
    "fuel_economy_kmpl": 15.0,
    "co2_g_per_km": 120.0,
}

STATIC_POINTS = {
    "From": {
        "Kolkata (Esplanade)": (22.5667, 88.3667),
        "Delhi (Connaught Place)": (28.6315, 77.2167),
        "Mumbai (Fort/CST)": (18.9399, 72.8355),
        "Bengaluru (MG Road)": (12.9759, 77.6050),
    },
    "To": {
        "Chennai (Central area)": (13.0827, 80.2707),
        "Hyderabad (Charminar)": (17.3616, 78.4747),
        "Pune (Shivajinagar)": (18.5308, 73.8470),
        "Guwahati (Paltan Bazar)": (26.1754, 91.7450),
    },
}

st.set_page_config(page_title="India Route Optimizer", layout="wide")
st.title("India Route Optimizer (Road) — Emissions, Cost, Time, Distance")
st.caption("ORS Directions with automatic fallback for long distances (no Google Maps).")

ORS_API_KEY = st.secrets.get("ORS_API_KEY", "")
client = ORSClient(ORS_API_KEY)

left, right = st.columns(2)
with left:
    use_static = st.checkbox("Use static India points", value=True)
    if use_static:
        orig_label = st.selectbox("From", list(STATIC_POINTS["From"].keys()))
        dest_label = st.selectbox("To", list(STATIC_POINTS["To"].keys()))
        origin = STATIC_POINTS["From"][orig_label]
        dest = STATIC_POINTS["To"][dest_label]
    else:
        origin = (
            st.number_input("From Lat", value=22.5667, format="%.6f"),
            st.number_input("From Lon", value=88.3667, format="%.6f")
        )
        dest = (
            st.number_input("To Lat", value=13.0827, format="%.6f"),
            st.number_input("To Lon", value=80.2707, format="%.6f")
        )

with right:
    st.subheader("Vehicle & Optimization Settings")
    co2_g_km = st.number_input("CO₂ intensity (g/km)", value=float(DEFAULTS["co2_g_per_km"]))
    fuel_economy = st.number_input("Fuel economy (km/litre)", value=float(DEFAULTS["fuel_economy_kmpl"]))
    fuel_price = st.number_input("Fuel price (₹/litre)", value=float(DEFAULTS["fuel_price_inr_per_litre"]))
    alt_count = st.slider("Number of alternatives (≤150km)", 1, 5, 3)
    avoid_tolls = st.checkbox("Avoid tollways", value=False)
    weights = {
        "distance_km": st.slider("Weight: distance", 0.0, 3.0, 1.0),
        "duration_min": st.slider("Weight: time", 0.0, 3.0, 1.0),
        "cost_inr": st.slider("Weight: cost", 0.0, 3.0, 1.0),
        "emissions_kg": st.slider("Weight: emissions", 0.0, 3.0, 1.0),
    }

if not ORS_API_KEY:
    st.warning("Set ORS_API_KEY in Streamlit Cloud → App settings → Secrets.")

if st.button("Find & Optimize Routes"):
    try:
        if origin == dest:
            st.error("Origin and destination are identical. Please choose different points.")
            st.stop()

        resp = client.fetch_routes(origin, dest, alt_count=alt_count, avoid_tolls=avoid_tolls)
        if isinstance(resp, dict) and resp.get('error'):
            st.error(resp['error'])
            st.json(resp)
            st.stop()

        routes = client.parse_routes(resp)
        if not routes:
            st.warning("No routes parsed from ORS response. Try changing points or check your API quota.")
            st.json(resp)
            st.stop()

        rows = []
        for i, r in enumerate(routes):
            dist = r.get("distance_km", 0.0)
            duration = r.get("duration_min", 0.0)
            cost_inr, emissions_kg = compute_cost_and_emissions(dist, fuel_economy, fuel_price, co2_g_km)
            rows.append({
                "route_id": i,
                "provider": r.get("provider", "ORS"),
                "distance_km": round(dist, 2),
                "duration_min": round(duration, 2),
                "cost_inr": cost_inr,
                "emissions_kg": emissions_kg,
                "num_steps": len(r.get("steps", [])),
            })
        df = pd.DataFrame(rows)

        scored_df, best_idx = score_routes(df, weights)
        st.subheader("All route alternatives / fastest fallback")
        st.dataframe(scored_df.style.highlight_min(subset=["score"], color="#d1ffd1"))

        st.subheader("Turn-by-turn details (street/highway names)")
        selected = int(scored_df.iloc[0]["route_id"]) if best_idx != -1 else 0
        steps_df = pd.DataFrame(routes[selected].get("steps", []))
        st.dataframe(steps_df)

        st.subheader("Map — optimized route highlighted")
        draw_routes_map(origin, dest, routes, selected)

        st.info("If crow-fly distance > 150 km, the app automatically requests a single fastest route due to ORS server limits on alternative routes.")

    except Exception as e:
        st.exception(e)
