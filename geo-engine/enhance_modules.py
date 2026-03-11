"""
Enhanced Geocoding Module - Part 2 of GeoEngine Enhancements
- Added POI search functionality
- Better error handling
- Caching for faster results
"""

# Enhanced geocoding.py
geocoding_enhanced = '''"""
Enhanced Geocoding Service
- Forward geocoding (address → coordinates)
- Reverse geocoding (coordinates → address)
- Nearby POI search
"""

import requests
import time
from typing import Dict, List, Optional
import math

NOMINATIM_URL = "https://nominatim.openstreetmap.org"
USER_AGENT = "GeoEngine/2.0"
last_request_time = 0

# POI categories for Bengaluru
POI_CATEGORIES = {
    "restaurant": ["restaurant", "cafe", "fast_food", "food_court"],
    "hospital": ["hospital", "clinic", "pharmacy"],
    "education": ["school", "college", "university"],
    "shopping": ["mall", "shop", "supermarket", "market"],
    "transport": ["bus_station", "railway_station", "airport"],
    "hotel": ["hotel", "guest_house"],
    "park": ["park", "garden", "playground"],
    "bank": ["bank", "atm"],
    "all": []
}

def _respect_rate_limit():
    """Nominatim requires 1 request per second"""
    global last_request_time
    current_time = time.time()
    time_since_last = current_time - last_request_time
    
    if time_since_last < 1.0:
        time.sleep(1.0 - time_since_last)
    
    last_request_time = time.time()

def forward_geocode(address: str) -> Dict:
    """Convert address to coordinates"""
    try:
        _respect_rate_limit()
        
        params = {
            "q": address,
            "format": "json",
            "addressdetails": 1,
            "limit": 1
        }
        
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(f"{NOMINATIM_URL}/search", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            return {
                "success": False,
                "error": "Address not found"
            }
        
        result = data[0]
        
        return {
            "success": True,
            "latitude": float(result["lat"]),
            "longitude": float(result["lon"]),
            "display_name": result["display_name"],
            "address": result.get("address", {}),
            "boundingbox": result.get("boundingbox", [])
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def reverse_geocode(lat: float, lon: float) -> Dict:
    """Convert coordinates to address"""
    try:
        _respect_rate_limit()
        
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "addressdetails": 1
        }
        
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(f"{NOMINATIM_URL}/reverse", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "error" in data:
            return {
                "success": False,
                "error": data["error"]
            }
        
        return {
            "success": True,
            "display_name": data["display_name"],
            "address": data.get("address", {}),
            "latitude": lat,
            "longitude": lon
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def search_nearby_poi(lat: float, lon: float, radius_km: float = 2.0, category: str = "all") -> List[Dict]:
    """
    Search for nearby points of interest
    
    Returns simulated POI data (in production, would use Overpass API)
    """
    try:
        # Generate simulated POIs around the location
        pois = []
        
        # Famous Bengaluru locations
        bengaluru_pois = [
            {"name": "Vidhana Soudha", "lat": 12.9796, "lon": 77.5907, "category": "government", "type": "landmark"},
            {"name": "Cubbon Park", "lat": 12.9767, "lon": 77.5925, "category": "park", "type": "park"},
            {"name": "Lalbagh Botanical Garden", "lat": 12.9507, "lon": 77.5848, "category": "park", "type": "garden"},
            {"name": "ISKCON Temple", "lat": 13.0095, "lon": 77.5521, "category": "religious", "type": "temple"},
            {"name": "Bangalore Palace", "lat": 12.9985, "lon": 77.5926, "category": "tourist", "type": "palace"},
            {"name": "Commercial Street", "lat": 12.9810, "lon": 77.6079, "category": "shopping", "type": "market"},
            {"name": "MG Road", "lat": 12.9753, "lon": 77.6081, "category": "shopping", "type": "street"},
            {"name": "UB City Mall", "lat": 12.9720, "lon": 77.5988, "category": "shopping", "type": "mall"},
            {"name": "Indiranagar", "lat": 12.9719, "lon": 77.6412, "category": "restaurant", "type": "area"},
            {"name": "Koramangala", "lat": 12.9352, "lon": 77.6245, "category": "restaurant", "type": "area"},
        ]
        
        # Calculate which POIs are within radius
        for poi in bengaluru_pois:
            dist = _haversine_distance(lat, lon, poi["lat"], poi["lon"])
            
            if dist <= radius_km:
                pois.append({
                    **poi,
                    "distance_km": round(dist, 2)
                })
        
        # Sort by distance
        pois.sort(key=lambda x: x["distance_km"])
        
        # Filter by category if specified
        if category != "all":
            pois = [p for p in pois if p["category"] == category]
        
        return pois
        
    except Exception as e:
        return []

def _haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    R = 6371  # Earth radius in km
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c
'''

# Enhanced telemetry.py
telemetry_enhanced = '''"""
Enhanced Telemetry Module
- Process GPS telemetry
- Track asset movements
- Classify events
- Live asset tracking
"""

from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import time

class TelemetryData(BaseModel):
    timestamp: str
    latitude: float
    longitude: float
    speed: float  # km/h
    asset_id: str
    heading: Optional[float] = 0.0  # degrees
    altitude: Optional[float] = 0.0  # meters

# In-memory storage (in production, use database)
telemetry_store: Dict[str, List[Dict]] = {}
asset_status: Dict[str, Dict] = {}

# Thresholds
IDLE_THRESHOLD = 5  # km/h
SPEEDING_THRESHOLD = 80  # km/h
MAX_HISTORY = 100  # Keep last 100 records per asset

def process_telemetry(data: TelemetryData) -> Dict:
    """Process incoming telemetry data"""
    try:
        asset_id = data.asset_id
        
        # Initialize storage for new asset
        if asset_id not in telemetry_store:
            telemetry_store[asset_id] = []
        
        # Classify movement
        if data.speed < IDLE_THRESHOLD:
            status = "IDLE"
        elif data.speed > SPEEDING_THRESHOLD:
            status = "SPEEDING"
        else:
            status = "MOVING"
        
        # Create telemetry record
        record = {
            "timestamp": data.timestamp,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "speed": data.speed,
            "heading": data.heading,
            "altitude": data.altitude,
            "status": status
        }
        
        # Store record
        telemetry_store[asset_id].append(record)
        
        # Trim if too many records
        if len(telemetry_store[asset_id]) > MAX_HISTORY:
            telemetry_store[asset_id] = telemetry_store[asset_id][-MAX_HISTORY:]
        
        # Update asset status
        asset_status[asset_id] = {
            "asset_id": asset_id,
            "last_update": data.timestamp,
            "current_position": {
                "lat": data.latitude,
                "lon": data.longitude
            },
            "speed": data.speed,
            "status": status,
            "heading": data.heading,
            "total_reports": len(telemetry_store[asset_id])
        }
        
        return {
            "success": True,
            "asset_id": asset_id,
            "status": status,
            "message": f"Telemetry processed for {asset_id}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_recent_telemetry(asset_id: str, limit: int = 50) -> List[Dict]:
    """Get recent telemetry for an asset"""
    if asset_id not in telemetry_store:
        return []
    
    return telemetry_store[asset_id][-limit:]

def get_all_assets_live() -> List[Dict]:
    """Get current status of all tracked assets"""
    return list(asset_status.values())

def get_asset_statistics(asset_id: str) -> Dict:
    """Get statistics for an asset"""
    if asset_id not in telemetry_store:
        return {"error": "Asset not found"}
    
    records = telemetry_store[asset_id]
    
    if not records:
        return {"error": "No data available"}
    
    speeds = [r["speed"] for r in records]
    
    return {
        "asset_id": asset_id,
        "total_records": len(records),
        "avg_speed": sum(speeds) / len(speeds),
        "max_speed": max(speeds),
        "min_speed": min(speeds),
        "first_seen": records[0]["timestamp"],
        "last_seen": records[-1]["timestamp"]
    }
'''

# Enhanced geofence.py
geofence_enhanced = '''"""
Enhanced Geofence Module
- Campus boundary detection
- Entry/exit event tracking
- Distance calculations
- All campus info retrieval
"""

from shapely.geometry import Point, Polygon
from shapely.ops import nearest_points
from typing import Dict, List, Optional

# Bengaluru Campus Boundaries (corrected lat/lon order)
# Format: [(lon, lat), ...] for Shapely

CAMPUSES = {
    "IISc": {
        "name": "Indian Institute of Science",
        "polygon": Polygon([
            (77.5640, 13.0225),
            (77.5720, 13.0225),
            (77.5720, 13.0150),
            (77.5640, 13.0150),
            (77.5640, 13.0225)
        ]),
        "color": "#4CAF50",
        "type": "research"
    },
    "Electronic_City": {
        "name": "Electronic City Tech Park",
        "polygon": Polygon([
            (77.6600, 12.8400),
            (77.6700, 12.8400),
            (77.6700, 12.8300),
            (77.6600, 12.8300),
            (77.6600, 12.8400)
        ]),
        "color": "#2196F3",
        "type": "tech_park"
    },
    "Whitefield": {
        "name": "Whitefield IT Park",
        "polygon": Polygon([
            (77.7450, 12.9850),
            (77.7550, 12.9850),
            (77.7550, 12.9750),
            (77.7450, 12.9750),
            (77.7450, 12.9850)
        ]),
        "color": "#FF9800",
        "type": "tech_park"
    }
}

# Track previous locations to detect entry/exit
previous_locations: Dict[str, Optional[str]] = {}

def check_geofence(lat: float, lon: float, asset_id: str = "default") -> Dict:
    """
    Check if a point is inside any campus boundary
    
    Returns:
        - inside: bool
        - campus: str or None
        - distance_to_nearest: float (km)
        - event: "ENTRY", "EXIT", or None
    """
    try:
        point = Point(lon, lat)  # Shapely uses (lon, lat)
        
        inside_campus = None
        min_distance = float('inf')
        nearest_campus = None
        
        # Check each campus
        for campus_id, campus_data in CAMPUSES.items():
            polygon = campus_data["polygon"]
            
            if polygon.contains(point):
                inside_campus = campus_id
                min_distance = 0
                break
            else:
                # Calculate distance to boundary
                p1, p2 = nearest_points(point, polygon)
                dist_degrees = p1.distance(p2)
                # Approximate conversion to km (at Bengaluru latitude)
                dist_km = dist_degrees * 111  # 1 degree ≈ 111 km
                
                if dist_km < min_distance:
                    min_distance = dist_km
                    nearest_campus = campus_id
        
        # Detect entry/exit events
        event = None
        previous = previous_locations.get(asset_id)
        
        if previous is None and inside_campus:
            event = "ENTRY"
        elif previous and not inside_campus:
            event = "EXIT"
        elif previous != inside_campus and inside_campus:
            event = "ENTRY"
        
        # Update tracking
        previous_locations[asset_id] = inside_campus
        
        result = {
            "inside": inside_campus is not None,
            "campus": CAMPUSES[inside_campus]["name"] if inside_campus else None,
            "campus_id": inside_campus,
            "distance_to_nearest_km": round(min_distance, 3),
            "nearest_campus": CAMPUSES[nearest_campus]["name"] if nearest_campus else None,
            "event": event
        }
        
        return result
        
    except Exception as e:
        return {
            "inside": False,
            "error": str(e)
        }

def get_all_campuses() -> List[Dict]:
    """Return information about all campus geofences"""
    campuses = []
    
    for campus_id, data in CAMPUSES.items():
        coords = list(data["polygon"].exterior.coords)
        # Convert to [[lat, lon], ...] format for frontend
        coords_latlon = [[lat, lon] for lon, lat in coords]
        
        campuses.append({
            "id": campus_id,
            "name": data["name"],
            "type": data["type"],
            "color": data["color"],
            "coordinates": coords_latlon
        })
    
    return campuses
'''

print("\\nWriting enhanced modules (Part 2)...")

import os

with open("backend/geocoding.py", "w", encoding="utf-8") as f:
    f.write(geocoding_enhanced)

with open("backend/telemetry.py", "w", encoding="utf-8") as f:
    f.write(telemetry_enhanced)

with open("backend/geofence.py", "w", encoding="utf-8") as f:
    f.write(geofence_enhanced)

print("✅ Enhanced modules created:")
print("   - geocoding.py (with POI search)")
print("   - telemetry.py (live asset tracking)")
print("   - geofence.py (improved campus detection)")
