"""
Create Complete Routing Module for Bengaluru
"""

def create_routing():
    with open("backend/routing.py", "w", encoding="utf-8") as f:
        f.write('''"""
Intelligent Routing Engine
GeoEngine - Bengaluru, India

This module handles route calculation using OpenStreetMap data.
Uses OSMNX to download road network data and NetworkX for pathfinding.

Key features:
- Downloads and caches OSM data for Bengaluru
- Uses A* algorithm for optimal route finding
- Calculates distance and estimated travel time
- Returns list of GPS waypoints along the route

The graph is downloaded once and cached to data/osm_data/bengaluru_network.pkl
"""

import osmnx as ox
import networkx as nx
from typing import List, Tuple, Dict
import pickle
import os
from math import radians, cos, sin, asin, sqrt

# Configuration
BENGALURU_CENTER = (12.9716, 77.5946)  # Bengaluru city center coordinates
BENGALURU_DIST = 15000  # Download area radius in meters (15km)
CACHE_DIR = "../data/osm_data"
CACHE_FILE = os.path.join(CACHE_DIR, "bengaluru_network.pkl")

# Global variable to store the loaded graph
ROAD_GRAPH = None


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth
    
    Uses the Haversine formula to calculate distance in kilometers.
    This is used as a heuristic for A* algorithm.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
    
    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lon1_rad, lat1_rad, lon2_rad, lat2_rad = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    delta_lon = lon2_rad - lon1_rad
    delta_lat = lat2_rad - lat1_rad
    area = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
    central_angle = 2 * asin(sqrt(area))
    
    # Earth radius in kilometers
    earth_radius_km = 6371
    
    distance_km = earth_radius_km * central_angle
    return distance_km


def _download_and_cache_graph() -> nx.MultiDiGraph:
    """
    Download road network from OpenStreetMap and cache it locally
    
    Downloads the road network for Bengaluru area using OSMNX.
    The graph is saved as a pickle file to avoid re-downloading.
    
    Returns:
        NetworkX MultiDiGraph representing the road network
    """
    print("Downloading OpenStreetMap data for Bengaluru...")
    print(f"Center: {BENGALURU_CENTER}, Radius: {BENGALURU_DIST}m")
    
    # Download road network from OSM (network_type='drive' gets roads accessible by cars)
    graph = ox.graph_from_point(
        BENGALURU_CENTER, 
        dist=BENGALURU_DIST, 
        network_type='drive',
        simplify=True
    )
    
    # Create cache directory if it doesn't exist
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # Save graph to cache file
    with open(CACHE_FILE, 'wb') as cache_file:
        pickle.dump(graph, cache_file)
    
    print(f"Graph downloaded and cached: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    return graph


def _load_graph() -> nx.MultiDiGraph:
    """
    Load road network graph from cache or download if not cached
    
    Returns:
        NetworkX MultiDiGraph representing the road network
    """
    global ROAD_GRAPH
    
    # Return cached graph if already loaded
    if ROAD_GRAPH is not None:
        return ROAD_GRAPH
    
    # Try to load from cache file
    if os.path.exists(CACHE_FILE):
        print(f"Loading cached road network from {CACHE_FILE}")
        with open(CACHE_FILE, 'rb') as cache_file:
            ROAD_GRAPH = pickle.load(cache_file)
        print(f"Graph loaded: {len(ROAD_GRAPH.nodes)} nodes")
        return ROAD_GRAPH
    
    # Download and cache if not found
    ROAD_GRAPH = _download_and_cache_graph()
    return ROAD_GRAPH


def compute_route(start_lat: float, start_lon: float, 
                 end_lat: float, end_lon: float) -> Dict:
    """
    Calculate optimal route between two GPS coordinates
    
    Uses A* algorithm to find the shortest path in the road network.
    The algorithm uses length (distance) as the weight and haversine
    distance as the heuristic for faster pathfinding.
    
    Args:
        start_lat: Starting latitude
        start_lon: Starting longitude
        end_lat: Ending latitude
        end_lon: Ending longitude
    
    Returns:
        Dictionary containing:
            - route: List of [lat, lon] coordinate pairs
            - distance_km: Total route distance in kilometers
            - estimated_time_min: Estimated travel time in minutes
    """
    # Load the road network graph
    graph = _load_graph()
    
    # Find nearest nodes in the graph to start and end coordinates
    start_node = ox.distance.nearest_nodes(graph, start_lon, start_lat)
    end_node = ox.distance.nearest_nodes(graph, end_lon, end_lat)
    
    print(f"Computing route from node {start_node} to {end_node}")
    
    # Use A* algorithm to find shortest path (weight='length' uses edge length in meters as cost)
    try:
        path_nodes = nx.astar_path(
            graph, 
            start_node, 
            end_node, 
            weight='length',
            heuristic=lambda node1, node2: _haversine_distance(
                graph.nodes[node1]['y'], graph.nodes[node1]['x'],
                graph.nodes[node2]['y'], graph.nodes[node2]['x']
            ) * 1000  # Convert km to meters for consistency
        )
    except nx.NetworkXNoPath:
        raise Exception("No route found between the given coordinates")
    
    # Extract route coordinates from path nodes
    route_coords = []
    for node_id in path_nodes:
        node_data = graph.nodes[node_id]
        route_coords.append([node_data['y'], node_data['x']])  # [lat, lon]
    
    # Calculate total distance
    total_distance_meters = 0
    for index in range(len(path_nodes) - 1):
        # Get edge data between consecutive nodes
        edge_data = graph[path_nodes[index]][path_nodes[index + 1]]
        # Take the first edge if multiple edges exist
        edge_length = list(edge_data.values())[0].get('length', 0)
        total_distance_meters += edge_length
    
    distance_km = total_distance_meters / 1000
    
    # Estimate travel time (assuming average speed of 30 km/h in city traffic)
    average_speed_kmh = 30
    estimated_time_min = (distance_km / average_speed_kmh) * 60
    
    print(f"Route calculated: {distance_km:.2f} km, {estimated_time_min:.1f} minutes")
    
    return {
        "route": route_coords,
        "distance_km": round(distance_km, 2),
        "estimated_time_min": round(estimated_time_min, 1)
    }
''')
    
    print("✅ routing.py created successfully for Bengaluru!")

if __name__ == "__main__":
    create_routing()
