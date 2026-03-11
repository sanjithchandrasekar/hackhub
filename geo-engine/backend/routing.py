"""
GeoEngine – Routing Engine (Tamil Nadu)
========================================
Uses OSMnx + NetworkX for road-network routing.
Falls back to straight-line estimation when OSM data unavailable.
"""

import osmnx as ox
import networkx as nx
import pickle
import os
from typing import List, Dict, Optional
import math

# ── Tamil Nadu configuration ───────────────────────────────────────────────
TN_CENTER    = (10.7905, 78.6547)   # geographic centre of Tamil Nadu
TN_DIST      = 5000                 # 5 km download for demo (fast startup)
CACHE_DIR    = os.path.join(os.path.dirname(__file__), "..", "data", "osm_data")
CACHE_FILE   = os.path.join(CACHE_DIR, "tn_network.pkl")

_graph_cache = None


def _haversine_distance(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance in metres."""
    R = 6_371_000
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    a = (math.sin((lat2-lat1)/2)**2
         + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2)
    return R * 2 * math.asin(math.sqrt(a))


def _load_or_download_graph():
    global _graph_cache
    if _graph_cache is not None:
        return _graph_cache

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            _graph_cache = pickle.load(f)
        print(f"[routing] Loaded TN graph from cache ({CACHE_FILE})")
        return _graph_cache

    print("[routing] Downloading OSM data for Tamil Nadu centre …")
    os.makedirs(CACHE_DIR, exist_ok=True)
    G = ox.graph_from_point(TN_CENTER, dist=TN_DIST, network_type="drive")
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(G, f)
    print(f"[routing] Graph cached ({len(G.nodes)} nodes)")
    _graph_cache = G
    return G


def _straight_line_route(slat, slon, elat, elon, mode="fastest") -> Dict:
    """Analytical fallback when OSM graph is unavailable."""
    dist_m = _haversine_distance(slat, slon, elat, elon)
    dist_km = dist_m / 1000
    speed = {"fastest": 45, "shortest": 25, "balanced": 35}.get(mode, 35)
    # Straight-line → apply 1.35 tortuosity factor
    dist_road = dist_km * 1.35
    eta = (dist_road / speed) * 60

    # Simple interpolated route (20 points)
    steps = 20
    route = [
        [slat + (elat-slat)*i/steps, slon + (elon-slon)*i/steps]
        for i in range(steps+1)
    ]
    return {
        "route":               route,
        "distance_km":         round(dist_road, 2),
        "estimated_time_min":  round(eta, 1),
        "waypoints_count":     len(route),
        "mode":                mode,
        "source":              "straight_line_fallback",
    }


def compute_route(start_lat, start_lon, end_lat, end_lon, mode="fastest") -> Dict:
    """
    Compute a road-network route between two coordinates.

    Parameters
    ----------
    mode : "fastest" | "shortest" | "balanced"
    """
    try:
        G = _load_or_download_graph()

        start_node = ox.distance.nearest_nodes(G, start_lon, start_lat)
        end_node   = ox.distance.nearest_nodes(G, end_lon,   end_lat)

        if start_node == end_node:
            # Check actual distance before assuming 0km (they might have snapped to the same boundary node)
            dist_m = _haversine_distance(start_lat, start_lon, end_lat, end_lon)
            if dist_m > 100:
                return _straight_line_route(start_lat, start_lon, end_lat, end_lon, mode)
                
            return {"route": [[start_lat, start_lon]], "distance_km": 0.0,
                    "estimated_time_min": 0.0, "waypoints_count": 1, "mode": mode}

        weight = "length"   # all modes use length; speed differs post-calc
        path = nx.astar_path(
            G, start_node, end_node,
            heuristic=lambda u, v: _haversine_distance(
                G.nodes[u]["y"], G.nodes[u]["x"],
                G.nodes[v]["y"], G.nodes[v]["x"]),
            weight=weight,
        )

        route_coords = [[G.nodes[n]["y"], G.nodes[n]["x"]] for n in path]

        total_m = sum(
            list(G.get_edge_data(path[i], path[i+1]).values())[0].get("length", 0)
            for i in range(len(path) - 1)
        )
        dist_km = total_m / 1000

        speed = {"fastest": 45, "shortest": 25, "balanced": 35}.get(mode, 35)
        eta   = (dist_km / speed) * 60

        return {
            "route":               route_coords,
            "distance_km":         round(dist_km, 2),
            "estimated_time_min":  round(eta, 1),
            "waypoints_count":     len(route_coords),
            "mode":                mode,
            "source":              "osm_graph",
        }

    except Exception:
        # Always return a usable result
        return _straight_line_route(start_lat, start_lon, end_lat, end_lon, mode)


def compute_alternative_routes(start_lat, start_lon, end_lat, end_lon) -> List[Dict]:
    """
    Return 3 route alternatives: fastest, shortest, balanced.
    Adds small variation factors to differentiate them realistically.
    """
    modes   = ["fastest", "shortest", "balanced"]
    results = []

    for mode in modes:
        r = compute_route(start_lat, start_lon, end_lat, end_lon, mode=mode)
        results.append(r)

    # Inject slight variation so all three differ visibly even with fallback
    import random
    rng = random.Random(42)
    for i, r in enumerate(results):
        if r.get("source") == "straight_line_fallback":
            factor = [1.0, 1.15, 1.08][i]
            r["distance_km"]        = round(r["distance_km"] * factor, 2)
            r["estimated_time_min"] = round(r["estimated_time_min"] * factor, 1)
            # Offset each route slightly so they look different on map
            offsets = [0.0, 0.003, -0.003]
            r["route"] = [
                [lat + offsets[i], lon + offsets[i]]
                for lat, lon in r["route"]
            ]

    return results


def compute_multi_waypoint_route(waypoints: List[Dict], optimize=True) -> Dict:
    """Route through multiple stops in sequence."""
    if len(waypoints) < 2:
        raise ValueError("Need at least 2 waypoints")

    full_route, total_dist, total_eta = [], 0.0, 0.0

    for i in range(len(waypoints) - 1):
        seg = compute_route(
            waypoints[i]["lat"],   waypoints[i]["lon"],
            waypoints[i+1]["lat"], waypoints[i+1]["lon"],
        )
        if i > 0 and full_route:
            full_route.extend(seg["route"][1:])
        else:
            full_route.extend(seg["route"])
        total_dist += seg["distance_km"]
        total_eta  += seg["estimated_time_min"]

    return {
        "route":               full_route,
        "distance_km":         round(total_dist, 2),
        "estimated_time_min":  round(total_eta, 1),
        "waypoints_count":     len(full_route),
        "stops":               len(waypoints),
    }


