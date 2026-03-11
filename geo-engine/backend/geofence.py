"""
GeoEngine - Geofence Module (Tamil Nadu)
=========================================
Polygon-based geofencing for Tamil Nadu campuses / zones.
Tracks entry and exit events per asset_id.
"""

from shapely.geometry import Point, Polygon
from shapely.ops import nearest_points
from typing import Dict, List, Optional

#  Tamil Nadu campus / zone boundaries 
# Shapely uses (lon, lat) order
CAMPUSES = {
    "IIT_Madras": {
        "name":    "IIT Madras",
        "polygon": Polygon([
            (80.2316, 13.0108),
            (80.2390, 13.0108),
            (80.2390, 13.0048),
            (80.2316, 13.0048),
            (80.2316, 13.0108),
        ]),
        "color": "#4CAF50",
        "type":  "university",
    },
    "Anna_University": {
        "name":    "Anna University",
        "polygon": Polygon([
            (80.2340, 13.0112),
            (80.2400, 13.0112),
            (80.2400, 13.0060),
            (80.2340, 13.0060),
            (80.2340, 13.0112),
        ]),
        "color": "#2196F3",
        "type":  "university",
    },
    "Tidel_Park": {
        "name":    "TIDEL Park Chennai",
        "polygon": Polygon([
            (80.2220, 12.9928),
            (80.2280, 12.9928),
            (80.2280, 12.9880),
            (80.2220, 12.9880),
            (80.2220, 12.9928),
        ]),
        "color": "#FF9800",
        "type":  "tech_park",
    },
    "PSG_Coimbatore": {
        "name":    "PSG Tech Park Coimbatore",
        "polygon": Polygon([
            (76.9530, 11.0070),
            (76.9610, 11.0070),
            (76.9610, 11.0010),
            (76.9530, 11.0010),
            (76.9530, 11.0070),
        ]),
        "color": "#9C27B0",
        "type":  "tech_park",
    },
    "NIT_Trichy": {
        "name":    "NIT Tiruchirappalli",
        "polygon": Polygon([
            (78.8150, 10.7630),
            (78.8230, 10.7630),
            (78.8230, 10.7570),
            (78.8150, 10.7570),
            (78.8150, 10.7630),
        ]),
        "color": "#F44336",
        "type":  "university",
    },
}

# Per-asset previous location for entry/exit detection
previous_locations: Dict[str, Optional[str]] = {}


def check_geofence(lat: float, lon: float, asset_id: str = "default") -> Dict:
    """
    Check whether (lat, lon) lies inside any campus polygon.

    Returns dict with keys:
      inside, campus, campus_id, distance_to_nearest_km,
      nearest_campus, event ("ENTRY" | "EXIT" | None)
    """
    point = Point(lon, lat)

    inside_campus = None
    min_dist_km   = float("inf")
    nearest_id    = None

    for cid, data in CAMPUSES.items():
        poly = data["polygon"]
        if poly.contains(point):
            inside_campus = cid
            min_dist_km   = 0.0
            break
        # Distance to boundary
        p1, p2 = nearest_points(point, poly)
        deg_dist = p1.distance(p2)
        km = deg_dist * 111.0
        if km < min_dist_km:
            min_dist_km = km
            nearest_id  = cid

    # Entry / exit detection
    event    = None
    previous = previous_locations.get(asset_id)
    if previous is None and inside_campus:
        event = "ENTRY"
    elif previous and not inside_campus:
        event = "EXIT"
    elif previous and inside_campus and previous != inside_campus:
        event = "ENTRY"

    previous_locations[asset_id] = inside_campus

    return {
        "inside":                 inside_campus is not None,
        "campus":                 CAMPUSES[inside_campus]["name"] if inside_campus else None,
        "campus_id":              inside_campus,
        "distance_to_nearest_km": round(min_dist_km, 3),
        "nearest_campus":         CAMPUSES[nearest_id]["name"] if nearest_id else None,
        "event":                  event,
    }


def get_all_campuses() -> List[Dict]:
    """Return campus metadata + polygon coordinates for the frontend."""
    result = []
    for cid, data in CAMPUSES.items():
        coords_latlon = [
            [lat, lon] for lon, lat in data["polygon"].exterior.coords
        ]
        result.append({
            "id":          cid,
            "name":        data["name"],
            "type":        data["type"],
            "color":       data["color"],
            "coordinates": coords_latlon,
        })
    return result
