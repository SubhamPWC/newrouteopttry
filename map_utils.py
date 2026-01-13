import folium
from streamlit_folium import st_folium

# Neon palette for high-contrast highlighting
RECOMMENDED_COLOR = "#00e5ff"   # cyan
ALT_COLORS = ["#ff1744", "#d500f9", "#69f0ae", "#ff9100", "#2a9df4"]

# Optional decoder for encoded polylines (not typical for ORS GeoJSON)
def _decode_polyline(polyline_str: str):
    coords = []
    index, lat, lng = 0, 0, 0
    length = len(polyline_str)
    while index < length:
        shift, result = 0, 0
        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat
        shift, result = 0, 0
        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng
        coords.append((lat / 1e5, lng / 1e5))
    return coords


def draw_routes_map(origin, dest, routes, recommended_index: int):
    """Dark map + layered highlight for recommended; vivid alternatives."""
    center_lat = (origin[0] + dest[0]) / 2.0
    center_lon = (origin[1] + dest[1]) / 2.0
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles="CartoDB dark_matter")

    # Start/End markers
    folium.CircleMarker(location=[origin[0], origin[1]], radius=6, color="#00e5ff", fill=True, fill_opacity=0.9, popup="From").add_to(m)
    folium.CircleMarker(location=[dest[0], dest[1]], radius=6, color="#ff9100", fill=True, fill_opacity=0.9, popup="To").add_to(m)

    for idx, r in enumerate(routes):
        geom = r.get("geometry", {})
        coords = []
        # ORS GeoJSON LineString uses [lon, lat]; folium expects [lat, lon]
        if isinstance(geom, dict) and geom.get("type") == "LineString":
            coords = [(lat, lon) for lon, lat in geom.get("coordinates", [])]
        elif isinstance(geom, dict) and geom.get("type") == "MultiLineString":
            for ln in geom.get("coordinates", []):
                coords.extend([(lat, lon) for lon, lat in ln])
        elif isinstance(geom, str) and geom:
            coords = _decode_polyline(geom)
        if not coords:
            continue

        if idx == recommended_index:
            # Shadow layer (glow) underneath
            folium.PolyLine(locations=coords, color="#000000", weight=12, opacity=0.45).add_to(m)
            # Bright top layer
            folium.PolyLine(
                locations=coords, color=RECOMMENDED_COLOR, weight=7, opacity=0.95,
                tooltip=f"Recommended • {r.get('distance_km',0):.1f} km, {r.get('duration_min',0):.1f} min"
            ).add_to(m)
        else:
            color = ALT_COLORS[idx % len(ALT_COLORS)]
            folium.PolyLine(
                locations=coords, color=color, weight=5, opacity=0.90,
                tooltip=f"Alternative {idx} • {r.get('distance_km',0):.1f} km, {r.get('duration_min',0):.1f} min"
            ).add_to(m)

    return st_folium(m, height=600)
