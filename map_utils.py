import folium
from streamlit_folium import st_folium

# Palette
RECOMMENDED_COLOR = "#3b82f6"  # bright blue
ALT_COLORS = ["#ff1744", "#00e5ff", "#d500f9", "#69f0ae", "#ff9100", "#2a9df4"]


def _style_function_factory(color: str, weight: int = 6, opacity: float = 0.95):
    def _style(_):
        return {
            'color': color,
            'weight': weight,
            'opacity': opacity
        }
    return _style


def draw_routes_map(origin, dest, routes, recommended_index: int):
    """Draw routes using GeoJSON (lets Leaflet handle [lon, lat] properly)."""
    center_lat = (origin[0] + dest[0]) / 2.0
    center_lon = (origin[1] + dest[1]) / 2.0
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles="CartoDB dark_matter")

    # Start/End markers
    folium.CircleMarker(location=[origin[0], origin[1]], radius=6, color="#00e5ff", fill=True, fill_opacity=0.9, popup="From").add_to(m)
    folium.CircleMarker(location=[dest[0], dest[1]], radius=6, color="#ff9100", fill=True, fill_opacity=0.9, popup="To").add_to(m)

    for idx, r in enumerate(routes):
        geom = r.get('geometry')
        if not isinstance(geom, dict):
            continue
        rec = (idx == recommended_index)
        color = RECOMMENDED_COLOR if rec else ALT_COLORS[idx % len(ALT_COLORS)]
        weight = 8 if rec else 5
        tooltip = f"{'Recommended' if rec else 'Alternative ' + str(idx)} • {r.get('distance_km',0):.1f} km, {r.get('duration_min',0):.1f} min"
        gj = folium.GeoJson(
            data=geom,
            style_function=_style_function_factory(color, weight=weight, opacity=0.95),
            name=f"route_{idx}"
        )
        gj.add_child(folium.Tooltip(tooltip))
        gj.add_to(m)

    folium.LayerControl().add_to(m)
    return st_folium(m, height=620)
