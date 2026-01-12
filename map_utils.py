import folium
from streamlit_folium import st_folium

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
    center_lat = (origin[0] + dest[0]) / 2.0
    center_lon = (origin[1] + dest[1]) / 2.0
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles="OpenStreetMap")

    folium.Marker(location=[origin[0], origin[1]], popup="From").add_to(m)
    folium.Marker(location=[dest[0], dest[1]], popup="To").add_to(m)

    for idx, r in enumerate(routes):
        color = "red" if idx == recommended_index else "blue"
        weight = 6 if idx == recommended_index else 3
        coords = []
        geom = r.get("geometry", {})
        if isinstance(geom, str) and geom:
            coords = _decode_polyline(geom)
        elif isinstance(geom, dict) and geom.get("type") == "LineString":
            coords = [(lat, lon) for lon, lat in geom.get("coordinates", [])]
        if coords:
            folium.PolyLine(locations=coords, color=color, weight=weight, opacity=0.9).add_to(m)

    return st_folium(m, height=560)
