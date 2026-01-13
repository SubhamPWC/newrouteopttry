import folium
from streamlit_folium import st_folium

# Neon palette for dark basemap
COLORS = {
    "recommended": "#ff1744",  # neon red
    "alt": ["#00e5ff", "#d500f9", "#69f0ae", "#ff9100"]  # cyan, magenta, lime, orange
}

# Optional decoder (kept for future OSRM support)
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


def _legend_html():
    return (
        """
        <div style="position: fixed; bottom: 20px; left: 20px; z-index: 9999; 
                    background: rgba(0,0,0,0.6); color:#fff; padding: 8px 10px; border-radius: 6px; font-size: 12px;">
            <b>Routes</b><br>
            <span style="color:#ff1744;">&#9632;</span> Recommended<br>
            <span style="color:#00e5ff;">&#9632;</span> Alternative 1<br>
            <span style="color:#d500f9;">&#9632;</span> Alternative 2<br>
            <span style="color:#69f0ae;">&#9632;</span> Alternative 3
        </div>
        """
    )


def draw_routes_map(origin, dest, routes, recommended_index: int):
    center_lat = (origin[0] + dest[0]) / 2.0
    center_lon = (origin[1] + dest[1]) / 2.0
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles="CartoDB dark_matter")

    # Start/End markers with neon icons
    folium.CircleMarker(location=[origin[0], origin[1]], radius=6, color="#00e5ff", fill=True, fill_opacity=0.9, popup="From").add_to(m)
    folium.CircleMarker(location=[dest[0], dest[1]], radius=6, color="#ff9100", fill=True, fill_opacity=0.9, popup="To").add_to(m)

    for idx, r in enumerate(routes):
        rec = (idx == recommended_index)
        color = COLORS["recommended"] if rec else COLORS["alt"][idx % len(COLORS["alt"])]
        # Simulate "glow" by adding a thicker, semi-transparent black path underneath
        geom = r.get("geometry", {})
        coords = []
        if isinstance(geom, str) and geom:
            coords = _decode_polyline(geom)
        elif isinstance(geom, dict) and geom.get("type") == "LineString":
            coords = [(lat, lon) for lon, lat in geom.get("coordinates", [])]
        elif isinstance(geom, dict) and geom.get("type") == "MultiLineString":
            for ln in geom.get("coordinates", []):
                coords = [(lat, lon) for lon, lat in ln]
        if coords:
            # Shadow layer
            folium.PolyLine(locations=coords, color="#000000", weight=10 if rec else 7, opacity=0.35).add_to(m)
            # Color layer
            folium.PolyLine(
                locations=coords, color=color, weight=7 if rec else 5, opacity=0.95,
                tooltip=f"Route {idx}: {r.get('distance_km',0):.1f} km, {r.get('duration_min',0):.1f} min"
            ).add_to(m)

    # Legend
    folium.map.Marker([center_lat, center_lon], icon=folium.DivIcon(html=_legend_html())).add_to(m)
    return st_folium(m, height=560)
