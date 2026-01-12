import requests
from typing import Dict, Any, List, Tuple

class ORSClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.openrouteservice.org/v2/directions/driving-car"

    def fetch_routes(self, origin: Tuple[float, float], dest: Tuple[float, float], alt_count: int = 3, avoid_tolls: bool = False) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "Missing ORS_API_KEY in Streamlit secrets."}
        headers = {"Authorization": self.api_key, "Content-Type": "application/json"}
        body = {
            "coordinates": [[origin[1], origin[0]], [dest[1], dest[0]]],
            "instructions": True,
            "extra_info": ["waytype", "tollways"],
            "preference": "recommended",
            "alternative_routes": {
                "share_factor": 0.6,
                "target_count": max(1, alt_count),
                "weight_factor": 1.4
            }
        }
        if avoid_tolls:
            body["options"] = {"avoid_features": ["tollways"]}
        try:
            resp = requests.post(self.url, json=body, headers=headers, timeout=60)
        except requests.RequestException as e:
            return {"error": f"Network error contacting ORS: {e}"}
        if not resp.ok:
            # Return ORS error message if present
            try:
                msg = resp.json().get('error', {}).get('message') or resp.text
            except Exception:
                msg = resp.text
            return {"error": f"ORS HTTP {resp.status_code}: {msg}"}
        try:
            return resp.json()
        except Exception:
            return {"error": "Failed to parse ORS JSON response."}

    @staticmethod
    def parse_routes(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not isinstance(resp, dict) or resp.get('error'):
            return []
        routes = []
        for feat in resp.get("features", []):
            props = feat.get("properties", {})
            segs = props.get("segments", [])
            steps_all = []
            for seg in segs:
                for s in seg.get("steps", []):
                    steps_all.append({
                        "instruction": s.get("instruction"),
                        "name": s.get("name"),
                        "distance_m": s.get("distance", 0),
                        "duration_s": s.get("duration", 0),
                    })
            routes.append({
                "distance_km": props.get("summary", {}).get("distance", 0)/1000.0,
                "duration_min": props.get("summary", {}).get("duration", 0)/60.0,
                "geometry": feat.get("geometry", {}),
                "steps": steps_all,
                "provider": "ORS"
            })
        return routes
