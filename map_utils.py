import folium
from streamlit_folium import st_folium

COLORS = ["#2a9df4", "#7e03a8", "#3cb371", "#ff7f0e"]  # blue, purple, green, orange

# Polyline decoder for OSRM-style polylines (kept for future extensions)
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
                    background: rgba(255,255,255,0.9); padding: 8px 10px; border-radius: 6px; font-size: 12px;">
            <b>Route Colors</b><br>
            <span style="color:#e31a1c;">&#9632;</span> Recommended<br>
            <span style="color:#2a9df4;">&#9632;</span> Alternative 1<br>
            <span style="color:#7e03a8;">&#9632;</span> Alternative 2<br>
            <span style="color:#3cb371;">&#9632;</span> Alternative 3
        </div>
        """
    )


def draw_routes_map(origin, dest, routes, recommended_index: int, title: str = None):
    center_lat = (origin[0] + dest[0]) / 2.0
    center_lon = (origin[1] + dest[1]) / 2.0
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles="OpenStreetMap")

    if title:
        folium.map.Marker([origin[0], origin[1]],
            icon=folium.DivIcon(html=f"<div style='font-weight:600;font-size:14px'>{title}</div>")
        ).add_to(m)

    folium.Marker(location=[origin[0], origin[1]], popup="From").add_to(m)
    folium.Marker(location=[dest[0], dest[1]], popup="To").add_to(m)

    # Draw alternatives
    for idx, r in enumerate(routes):
        rec = (idx == recommended_index)
        color = "#e31a1c" if rec else COLORS[idx % len(COLORS)]
        weight = 6 if rec else 3
        geom = r.get("geometry", {})
        coords = []
        if isinstance(geom, str) and geom:
            coords = _decode_polyline(geom)
        elif isinstance(geom, dict) and geom.get("type") == "LineString":
            coords = [(lat, lon) for lon, lat in geom.get("coordinates", [])]
        if coords:
            folium.PolyLine(
                locations=coords, color=color, weight=weight, opacity=0.9,
                tooltip=f"Route {idx}: {r.get('distance_km',0):.1f} km, {r.get('duration_min',0):.1f} min"
            ).add_to(m)

    # Legend
    folium.map.Marker([center_lat, center_lon], icon=folium.DivIcon(html=_legend_html())).add_to(m)
    return st_folium(m, height=520)
