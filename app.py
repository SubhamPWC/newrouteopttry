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
        "Bhubaneswar": (20.2961, 85.8250),
        "Chennai (Central area)": (13.0827, 80.2707),
        "Hyderabad (Charminar)": (17.3616, 78.4747),
        "Pune (Shivajinagar)": (18.5308, 73.8470),
        "Guwahati (Paltan Bazar)": (26.1754, 91.7450),
    },
}

st.set_page_config(page_title="Road Route Optimization (India)", layout="wide")
st.title("🚗 Road Route Optimization (India) — Distance · Time · Cost · Emissions")

# Sidebar
st.sidebar.header("Filters & Settings")
use_static = st.sidebar.checkbox("Use static India points", value=True)
if use_static:
    orig_label = st.sidebar.selectbox("From", list(STATIC_POINTS["From"].keys()), index=0)
    dest_label = st.sidebar.selectbox("To", list(STATIC_POINTS["To"].keys()), index=0)
    origin = STATIC_POINTS["From"][orig_label]
    dest = STATIC_POINTS["To"][dest_label]
else:
    origin = (
        st.sidebar.number_input("From Lat", value=22.5667, format="%.6f"),
        st.sidebar.number_input("From Lon", value=88.3667, format="%.6f")
    )
    dest = (
        st.sidebar.number_input("To Lat", value=20.2961, format="%.6f"),
        st.sidebar.number_input("To Lon", value=85.8250, format="%.6f")
    )

st.sidebar.markdown("---")
co2_g_km = st.sidebar.number_input("CO₂ intensity (g/km)", value=float(DEFAULTS["co2_g_per_km"]))
fuel_economy = st.sidebar.number_input("Fuel economy (km/litre)", value=float(DEFAULTS["fuel_economy_kmpl"]))
fuel_price = st.sidebar.number_input("Fuel price (₹/litre)", value=float(DEFAULTS["fuel_price_inr_per_litre"]))

st.sidebar.markdown("---")
alt_count = st.sidebar.slider("Alternatives (≤100 km)", 1, 5, 3)
avoid_tolls = st.sidebar.checkbox("Avoid tollways", value=False)
weights = {
    "distance_km": st.sidebar.slider("Weight: distance", 0.0, 3.0, 1.0),
    "duration_min": st.sidebar.slider("Weight: time", 0.0, 3.0, 1.0),
    "cost_inr": st.sidebar.slider("Weight: cost", 0.0, 3.0, 1.0),
    "emissions_kg": st.sidebar.slider("Weight: emissions", 0.0, 3.0, 1.0),
}

ORS_API_KEY = st.secrets.get("ORS_API_KEY", "")
if not ORS_API_KEY:
    st.sidebar.error("Set ORS_API_KEY in Streamlit Cloud → App settings → Secrets.")

run = st.sidebar.button("🔎 Find & Optimize Routes")

left, right = st.columns([1.25, 1])

@st.cache_data(show_spinner=False)
def _cached_fetch(origin, dest, alt_count, avoid_tolls, api_key):
    client = ORSClient(api_key)
    return client.fetch_routes(origin, dest, alt_count=alt_count, avoid_tolls=avoid_tolls)

# Initialize session_state containers
for key in ["routes", "scored_df", "best_idx", "origin", "dest", "message"]:
    if key not in st.session_state:
        st.session_state[key] = None

if run:
    try:
        if origin == dest:
            st.session_state.message = "Origin and destination are identical. Please choose different points."
        else:
            resp = _cached_fetch(origin, dest, alt_count, avoid_tolls, ORS_API_KEY)
            if isinstance(resp, dict) and resp.get('error'):
                st.session_state.message = resp['error']
                st.session_state.routes = None
            else:
                routes = ORSClient.parse_routes(resp)
                if not routes:
                    st.session_state.message = "No routes parsed from ORS response. Try changing points or check your API quota."
                    st.session_state.routes = None
                else:
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

                    st.session_state.routes = routes
                    st.session_state.scored_df = scored_df
                    st.session_state.best_idx = best_idx
                    st.session_state.origin = origin
                    st.session_state.dest = dest
                    st.session_state.message = None
    except Exception as e:
        st.session_state.message = f"Unexpected error: {e}"

# Always display current results if present (persist across reruns)
if st.session_state.message:
    st.error(st.session_state.message)

if st.session_state.routes and st.session_state.scored_df is not None:
    with left:
        rec_route_id = int(st.session_state.scored_df.iloc[0]["route_id"]) if st.session_state.best_idx != -1 else 0
        draw_routes_map(st.session_state.origin, st.session_state.dest, st.session_state.routes, rec_route_id)

    with right:
        st.subheader("Route Alternatives")
        st.dataframe(st.session_state.scored_df.style.highlight_min(subset=["score"], color="#d1ffd1"), use_container_width=True)

    st.subheader("✅ Recommended Route Details")
    selected = int(st.session_state.scored_df.iloc[0]["route_id"]) if st.session_state.best_idx != -1 else 0
    steps_df = pd.DataFrame(st.session_state.routes[selected].get("steps", []))
    if not steps_df.empty:
        steps_df = steps_df[["name", "instruction", "distance_m", "duration_s"]]
        steps_df.rename(columns={"name": "Road / Street", "instruction": "Instruction",
                                 "distance_m": "Segment (m)", "duration_s": "Segment (s)"}, inplace=True)
    st.dataframe(steps_df, use_container_width=True)

    st.success("Routes plotted and optimized. Adjust sidebar weights to change the recommendation.")
