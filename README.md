# India Route Optimizer (Streamlit, OSM-based) — Flat Repo

This Streamlit app fetches multiple **road route alternatives** (OpenStreetMap-based via OpenRouteService),
computes **cost (₹)** and **emissions (kg CO₂)**, optimizes by **distance / time / cost / emissions**, tags the
recommended route, and renders an interactive map with the optimized path.

> Designed for **Streamlit Community Cloud**: uses **OpenRouteService (ORS)**. No Google Maps.

## Quick start (local)
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Push these files to a public GitHub repo.
2. On https://share.streamlit.io -> **New app**
   - Repo: `your-username/your-repo`
   - Branch: `main`
   - Main file path: `app.py`
3. In **App settings → Secrets**, add:
```toml
ORS_API_KEY = "YOUR_ORS_API_KEY"
```
4. Deploy. The app will default to the **ORS** backend.

## Files
- `app.py` – Streamlit UI
- `multimodal.py` – ORS client + multimodal stubs
- `optimization.py` – ML-style weighted scoring & totals
- `map_utils.py` – Folium map rendering (with polyline decoder)
- `train_speed_model.py` – simple train model stub
- `requirements.txt` – dependencies

## Notes
- For **alternate routes with street/highway names**, ORS Directions API is used (`alternative_routes`).
- If you self-host **OSRM/GraphHopper**, wire them in `multimodal.py` (optional, not used on Cloud).
