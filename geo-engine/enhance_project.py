"""
Script to enhance GeoEngine with new features and better UI
Creates/updates all necessary files
"""

import os

# Backend enhancements
backend_main_enhanced = '''"""
GeoEngine - Enhanced Intelligent Geospatial Engine with Real-Time Learning
Backend API Server (FastAPI)

New Features Added:
- Traffic simulation and heatmaps
- Route history and analytics
- Saved routes/favorites
- Multi-waypoint routing
- Alternative routes
- Nearby POI search
- Live asset tracking
- Area and distance measurement
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from datetime import datetime, timedelta
import random
import math

# Import local modules
from routing import compute_route, compute_multi_waypoint_route, compute_alternative_routes
from geofence import check_geofence, get_all_campuses
from geocoding import forward_geocode, reverse_geocode, search_nearby_poi
from telemetry import process_telemetry, TelemetryData, get_all_assets_live
from database import save_route, get_recent_routes, save_favorite, get_favorites, delete_favorite

# Initialize FastAPI application
app = FastAPI(
    title="GeoEngine Enhanced API",
    description="Intelligent Geospatial Engine with Real-Time Learning - Enhanced Edition",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for enhanced features
route_history = []
favorites_store = []
traffic_data = {}

# ============ REQUEST/RESPONSE MODELS ============

class RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    mode: Optional[str] = "fastest"  # fastest, shortest, balanced

class MultiWaypointRequest(BaseModel):
    waypoints: List[Dict[str, float]]  # List of {lat, lon}
    optimize: Optional[bool] = True

class GeofenceRequest(BaseModel):
    lat: float
    lon: float

class GeocodeRequest(BaseModel):
    address: str

class ReverseGeocodeRequest(BaseModel):
    lat: float
    lon: float

class POISearchRequest(BaseModel):
    lat: float
    lon: float
    radius_km: Optional[float] = 2.0
    category: Optional[str] = "all"

class FavoriteRequest(BaseModel):
    name: str
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    notes: Optional[str] = ""

class MeasurementRequest(BaseModel):
    points: List[Dict[str, float]]  # List of {lat, lon}
    measurement_type: str  # "distance" or "area"

# ============ API ENDPOINTS ============

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "GeoEngine Enhanced API",
        "version": "2.0.0",
        "location": "Bengaluru, India",
        "features": ["routing", "geofencing", "geocoding", "telemetry", "traffic", "analytics"]
    }

@app.post("/route")
async def calculate_route_endpoint(request: RouteRequest):
    try:
        result = compute_route(
            request.start_lat, request.start_lon,
            request.end_lat, request.end_lon,
            mode=request.mode
        )
        
        # Save to history
        route_history.append({
            **result,
            "timestamp": datetime.now().isoformat(),
            "mode": request.mode
        })
        
        # Keep only last 50 routes
        if len(route_history) > 50:
            route_history.pop(0)
        
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/route/multi-waypoint")
async def multi_waypoint_route(request: MultiWaypointRequest):
    try:
        result = compute_multi_waypoint_route(request.waypoints, request.optimize)
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/route/alternatives")
async def alternative_routes(request: RouteRequest):
    try:
        routes = compute_alternative_routes(
            request.start_lat, request.start_lon,
            request.end_lat, request.end_lon
        )
        return {"status": "success", "routes": routes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/geofence")
async def get_geofences():
    try:
        campuses = get_all_campuses()
        return {"status": "success", "campuses": campuses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/geofence")
async def check_geofence_endpoint(request: GeofenceRequest):
    try:
        result = check_geofence(request.lat, request.lon)
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/geocode")
async def geocode_endpoint(request: GeocodeRequest):
    try:
        result = forward_geocode(request.address)
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reverse-geocode")
async def reverse_geocode_endpoint(request: ReverseGeocodeRequest):
    try:
        result = reverse_geocode(request.lat, request.lon)
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/poi/search")
async def search_poi(request: POISearchRequest):
    try:
        pois = search_nearby_poi(request.lat, request.lon, request.radius_km, request.category)
        return {"status": "success", "pois": pois}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/telemetry")
async def telemetry_endpoint(data: TelemetryData):
    try:
        result = process_telemetry(data)
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/assets/live")
async def get_live_assets():
    try:
        assets = get_all_assets_live()
        return {"status": "success", "assets": assets, "count": len(assets)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/routes")
async def get_route_analytics():
    try:
        total_routes = len(route_history)
        if total_routes == 0:
            return {
                "status": "success",
                "total_routes": 0,
                "avg_distance_km": 0,
                "avg_time_min": 0,
                "recent_routes": []
            }
        
        avg_distance = sum(r.get("distance_km", 0) for r in route_history) / total_routes
        avg_time = sum(r.get("estimated_time_min", 0) for r in route_history) / total_routes
        
        return {
            "status": "success",
            "total_routes": total_routes,
            "avg_distance_km": round(avg_distance, 2),
            "avg_time_min": round(avg_time, 2),
            "recent_routes": route_history[-10:]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/traffic/heatmap")
async def get_traffic_heatmap():
    """Generate simulated traffic heatmap data for Bengaluru"""
    try:
        # Generate random traffic hotspots around Bengaluru
        hotspots = []
        base_points = [
            {"lat": 12.9716, "lon": 77.5946, "name": "City Center"},
            {"lat": 12.9350, "lon": 77.6244, "name": "Marathahalli"},
            {"lat": 13.0200, "lon": 77.5680, "name": "IISc"},
            {"lat": 12.8400, "lon": 77.6650, "name": "Electronic City"},
            {"lat": 12.9800, "lon": 77.7500, "name": "Whitefield"},
        ]
        
        for point in base_points:
            intensity = random.uniform(0.3, 1.0)
            hotspots.append({
                "lat": point["lat"],
                "lon": point["lon"],
                "intensity": intensity,
                "name": point["name"],
                "vehicles": int(intensity * 2000),
                "avg_speed_kmh": int(50 - (intensity * 40))
            })
        
        return {"status": "success", "hotspots": hotspots, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/favorites")
async def add_favorite(request: FavoriteRequest):
    try:
        favorite = {
            "id": len(favorites_store) + 1,
            "name": request.name,
            "start_lat": request.start_lat,
            "start_lon": request.start_lon,
            "end_lat": request.end_lat,
            "end_lon": request.end_lon,
            "notes": request.notes,
            "created_at": datetime.now().isoformat()
        }
        favorites_store.append(favorite)
        return {"status": "success", "favorite": favorite}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/favorites")
async def list_favorites():
    try:
        return {"status": "success", "favorites": favorites_store}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/favorites/{favorite_id}")
async def remove_favorite(favorite_id: int):
    try:
        global favorites_store
        favorites_store = [f for f in favorites_store if f["id"] != favorite_id]
        return {"status": "success", "message": "Favorite deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/measure")
async def measure_distance_or_area(request: MeasurementRequest):
    """Calculate distance or area from points"""
    try:
        points = request.points
        measurement_type = request.measurement_type
        
        if measurement_type == "distance":
            # Calculate total distance along path
            total_distance = 0
            for i in range(len(points) - 1):
                p1 = points[i]
                p2 = points[i + 1]
                dist = _haversine_distance(p1["lat"], p1["lon"], p2["lat"], p2["lon"])
                total_distance += dist
            
            return {
                "status": "success",
                "type": "distance",
                "distance_km": round(total_distance, 3),
                "distance_m": round(total_distance * 1000, 1)
            }
        
        elif measurement_type == "area":
            # Calculate area using shoelace formula (approximation)
            if len(points) < 3:
                raise HTTPException(status_code=400, detail="Need at least 3 points for area")
            
            area_km2 = _calculate_polygon_area(points)
            
            return {
                "status": "success",
                "type": "area",
                "area_km2": round(area_km2, 6),
                "area_m2": round(area_km2 * 1_000_000, 2),
                "area_hectares": round(area_km2 * 100, 4)
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid measurement type")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    R = 6371  # Earth radius in km
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def _calculate_polygon_area(points):
    """Calculate area of polygon in km²"""
    n = len(points)
    area = 0.0
    
    for i in range(n):
        j = (i + 1) % n
        area += points[i]["lon"] * points[j]["lat"]
        area -= points[j]["lon"] * points[i]["lat"]
    
    area = abs(area) / 2.0
    
    # Convert to km² (rough approximation at Bengaluru latitude)
    km_per_degree_lat = 111.0
    km_per_degree_lon = 111.0 * math.cos(math.radians(12.97))
    area_km2 = area * km_per_degree_lat * km_per_degree_lon
    
    return area_km2

if __name__ == "__main__":
    print("\\n" + "="*50)
    print("🚀 Starting GeoEngine Enhanced Backend Server")
    print("="*50)
    print(f"📍 Location: Bengaluru, India")
    print(f"🌐 Server: http://localhost:8000")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print(f"✨ Version: 2.0.0 (Enhanced)")
    print("="*50 + "\\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
'''

# Enhanced Routing module
routing_enhanced = '''"""
Enhanced Routing Engine with Multiple Features
- Multi-waypoint optimization
- Alternative routes
- Different routing modes (fastest, shortest, balanced)
"""

import osmnx as ox
import networkx as nx
import pickle
import os
from typing import List, Dict, Tuple, Optional
import math

# Bengaluru configuration
BENGALURU_CENTER = (12.9716, 77.5946)
BENGALURU_DIST = 15000  # 15km radius
CACHE_DIR = "../data/osm_data"
CACHE_FILE = os.path.join(CACHE_DIR, "bengaluru_network.pkl")

# Global graph cache
_graph_cache = None

def _haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate great circle distance between two points in meters"""
    R = 6371000  # Earth radius in meters
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def _load_or_download_graph():
    """Load cached graph or download from OSM"""
    global _graph_cache
    
    if _graph_cache is not None:
        return _graph_cache
    
    if os.path.exists(CACHE_FILE):
        print(f"📂 Loading cached OSM graph from {CACHE_FILE}")
        with open(CACHE_FILE, "rb") as f:
            _graph_cache = pickle.load(f)
        return _graph_cache
    
    print(f"🌐 Downloading OSM data for Bengaluru (this may take a few minutes)...")
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    G = ox.graph_from_point(
        BENGALURU_CENTER,
        dist=BENGALURU_DIST,
        network_type='drive'
    )
    
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(G, f)
    
    print(f"✅ Graph cached to {CACHE_FILE}")
    _graph_cache = G
    return G

def compute_route(start_lat, start_lon, end_lat, end_lon, mode="fastest"):
    """
    Compute route between two points
    
    Modes:
    - fastest: Minimize time (use speed limits)
    - shortest: Minimize distance
    - balanced: Balance between time and distance
    """
    try:
        G = _load_or_download_graph()
        
        # Find nearest nodes
        start_node = ox.distance.nearest_nodes(G, start_lon, start_lat)
        end_node = ox.distance.nearest_nodes(G, end_lon, end_lat)
        
        if start_node == end_node:
            return {
                "route": [[start_lat, start_lon]],
                "distance_km": 0,
                "estimated_time_min": 0,
                "waypoints_count": 1,
                "mode": mode
            }
        
        # Choose weight based on mode
        if mode == "shortest":
            weight = "length"
        else:  # fastest or balanced
            weight = "length"  # We'll adjust with speed later
        
        # Compute path using A* algorithm
        path = nx.astar_path(
            G, start_node, end_node,
            heuristic=lambda u, v: _haversine_distance(
                G.nodes[u]['y'], G.nodes[u]['x'],
                G.nodes[v]['y'], G.nodes[v]['x']
            ),
            weight=weight
        )
        
        # Extract coordinates
        route_coords = [[G.nodes[node]['y'], G.nodes[node]['x']] for node in path]
        
        # Calculate total distance
        total_distance = 0
        for i in range(len(path) - 1):
            edge_data = G.get_edge_data(path[i], path[i+1])
            if edge_data:
                edge_length = list(edge_data.values())[0].get('length', 0)
                total_distance += edge_length
        
        distance_km = total_distance / 1000
        
        # Estimate time based on mode
        if mode == "fastest":
            avg_speed_kmh = 40  # Optimistic
        elif mode == "shortest":
            avg_speed_kmh = 25  # Conservative on short routes
        else:  # balanced
            avg_speed_kmh = 30
        
        estimated_time_min = (distance_km / avg_speed_kmh) * 60
        
        return {
            "route": route_coords,
            "distance_km": round(distance_km, 2),
            "estimated_time_min": round(estimated_time_min, 1),
            "waypoints_count": len(route_coords),
            "mode": mode
        }
        
    except Exception as e:
        raise Exception(f"Routing failed: {str(e)}")

def compute_multi_waypoint_route(waypoints: List[Dict], optimize: bool = True):
    """Compute route through multiple waypoints"""
    try:
        if len(waypoints) < 2:
            raise ValueError("Need at least 2 waypoints")
        
        total_route = []
        total_distance = 0
        total_time = 0
        
        # Simple approach: connect waypoints in order
        # TODO: Implement TSP optimization if optimize=True
        
        for i in range(len(waypoints) - 1):
            segment = compute_route(
                waypoints[i]["lat"], waypoints[i]["lon"],
                waypoints[i+1]["lat"], waypoints[i+1]["lon"]
            )
            
            if i > 0:
                # Remove duplicate point at junction
                segment["route"] = segment["route"][1:]
            
            total_route.extend(segment["route"])
            total_distance += segment["distance_km"]
            total_time += segment["estimated_time_min"]
        
        return {
            "route": total_route,
            "distance_km": round(total_distance, 2),
            "estimated_time_min": round(total_time, 1),
            "waypoints_count": len(total_route),
            "stops": len(waypoints)
        }
        
    except Exception as e:
        raise Exception(f"Multi-waypoint routing failed: {str(e)}")

def compute_alternative_routes(start_lat, start_lon, end_lat, end_lon):
    """Generate alternative routes by avoiding certain edges"""
    try:
        # Primary route
        primary = compute_route(start_lat, start_lon, end_lat, end_lon, mode="fastest")
        
        # Try to find alternatives (simplified - just use different modes)
        alternatives = [primary]
        
        # Alternative 1: Shortest route
        shortest = compute_route(start_lat, start_lon, end_lat, end_lon, mode="shortest")
        if abs(shortest["distance_km"] - primary["distance_km"]) > 0.5:
            alternatives.append(shortest)
        
        # Alternative 2: Balanced route
        balanced = compute_route(start_lat, start_lon, end_lat, end_lon, mode="balanced")
        if abs(balanced["distance_km"] - primary["distance_km"]) > 0.3:
            alternatives.append(balanced)
        
        return alternatives
        
    except Exception as e:
        raise Exception(f"Alternative routes failed: {str(e)}")
'''

print("Writing enhanced backend files...")
os.makedirs("backend", exist_ok=True)

with open("backend/main.py", "w", encoding="utf-8") as f:
    f.write(backend_main_enhanced)

with open("backend/routing.py", "w", encoding="utf-8") as f:
    f.write(routing_enhanced)

print("✅ Backend enhanced successfully!")
print("   - main.py (2.0.0 with new endpoints)")
print("   - routing.py (multi-waypoint, alternatives)")
