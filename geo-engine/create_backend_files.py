"""
Complete Backend File Generator for GeoEngine - Bengaluru
Generates all backend Python files with proper Bengaluru coordinates
"""

import os

def create_files():
    """Create all backend files"""
    
    # Ensure backend directory exists
    os.makedirs("backend", exist_ok=True)
    os.makedirs("data/osm_data", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    
    # File 1: geofence.py
    with open("backend/geofence.py", "w", encoding="utf-8") as f:
        f.write('''"""
Geofence Detection Module
GeoEngine - Bengaluru Campus Boundaries

This module handles geofence detection for 3 Bengaluru campuses:
1. IISc Campus (Indian Institute of Science)
2. Electronic City Tech Park
3. Whitefield Tech Park

Uses Shapely for point-in-polygon detection.
Returns inside/outside status, campus name, and distance to boundary.
"""

from shapely.geometry import Point, Polygon
from shapely.ops import nearest_points
from typing import Dict, Optional

# Campus boundary polygons with approximate real coordinates for Bengaluru
# Format: List of (longitude, latitude) points forming the polygon

# IISc Campus (Indian Institute of Science)
IISC_POLYGON = Polygon([
    (77.5640, 13.0225),
    (77.5720, 13.0225),
    (77.5720, 13.0150),
    (77.5640, 13.0150),
    (77.5640, 13.0225)
])

# Electronic City Tech Park
ELECTRONIC_CITY_POLYGON = Polygon([
    (77.6600, 12.8400),
    (77.6700, 12.8400),
    (77.6700, 12.8300),
    (77.6600, 12.8300),
    (77.6600, 12.8400)
])

# Whitefield Tech Park
WHITEFIELD_POLYGON = Polygon([
    (77.7450, 12.9850),
    (77.7550, 12.9850),
    (77.7550, 12.9750),
    (77.7450, 12.9750),
    (77.7450, 12.9850)
])

# Campus definitions
CAMPUSES = {
    "IISc Campus": IISC_POLYGON,
    "Electronic City": ELECTRONIC_CITY_POLYGON,
    "Whitefield Tech Park": WHITEFIELD_POLYGON
}

# Track previous location for entry/exit detection
previous_location = None


def check_geofence(lat: float, lon: float) -> Dict:
    """
    Check if GPS coordinates are inside any campus geofence
    
    Uses Shapely point-in-polygon algorithm to detect if a point
    is inside any of the defined campus boundaries.
    
    Args:
        lat: Latitude to check
        lon: Longitude to check
    
    Returns:
        Dictionary containing:
            - inside_geofence: Boolean, True if inside any campus
            - campus_name: String name of campus if inside, None otherwise
            - distance_to_nearest: Float distance in meters to nearest boundary
            - event_type: "ENTRY", "EXIT", or None
    """
    global previous_location
    
    # Create point from coordinates
    point = Point(lon, lat)  # Note: Shapely uses (x, y) = (lon, lat)
    
    # Check each campus
    inside_campus = None
    for campus_name, polygon in CAMPUSES.items():
        if polygon.contains(point):
            inside_campus = campus_name
            break
    
    # Calculate distance to nearest campus boundary
    nearest_dist = float('inf')
    for polygon in CAMPUSES.values():
        # Get nearest point on polygon boundary
        nearest_pt = nearest_points(point, polygon.boundary)[1]
        # Calculate distance in degrees, then convert to meters (approx)
        dist_degrees = point.distance(nearest_pt)
        dist_meters = dist_degrees * 111320  # 1 degree ≈ 111.32 km
        nearest_dist = min(nearest_dist, dist_meters)
    
    # Detect ENTRY or EXIT events
    event_type = None
    current_inside = inside_campus is not None
    
    if previous_location is not None:
        previous_inside = previous_location["inside"]
        
        if not previous_inside and current_inside:
            event_type = "ENTRY"
        elif previous_inside and not current_inside:
            event_type = "EXIT"
    
    # Update previous location
    previous_location = {
        "inside": current_inside,
        "campus": inside_campus
    }
    
    return {
        "inside_geofence": current_inside,
        "campus_name": inside_campus,
        "distance_to_nearest": round(nearest_dist, 2),
        "event_type": event_type
    }
''')
    
    # File 2: geocoding.py
    with open("backend/geocoding.py", "w", encoding="utf-8") as f:
        f.write('''"""
Geocoding Service Module
GeoEngine - Address <-> Coordinates Conversion

This module provides geocoding and reverse geocoding using Nominatim API.
- Forward geocoding: Convert address to GPS coordinates
- Reverse geocoding: Convert GPS coordinates to address

Uses OpenStreetMap's Nominatim service with proper rate limiting.
"""

import requests
import time
from typing import Dict, Optional

# Nominatim API configuration
NOMINATIM_URL = "https://nominatim.openstreetmap.org"
USER_AGENT = "GeoEngine/1.0 (Bengaluru Geospatial Engine)"
RATE_LIMIT_DELAY = 1.0  # Seconds between requests (Nominatim requirement)

# Track last request time for rate limiting
last_request_time = 0


def _respect_rate_limit():
    """
    Ensure we don't exceed Nominatim's rate limit of 1 request per second
    
    Waits if necessary to maintain proper spacing between requests.
    """
    global last_request_time
    
    # Calculate time since last request
    time_since_last = time.time() - last_request_time
    
    # Wait if we're making requests too quickly
    if time_since_last < RATE_LIMIT_DELAY:
        time.sleep(RATE_LIMIT_DELAY - time_since_last)
    
    # Update last request time
    last_request_time = time.time()


def forward_geocode(address: str) -> Optional[Dict]:
    """
    Convert address to GPS coordinates (forward geocoding)
    
    Uses Nominatim API to find coordinates for a given address.
    Best results with specific addresses including city and country.
    
    Args:
        address: Address string to geocode (e.g., "MG Road, Bengaluru, Karnataka")
    
    Returns:
        Dictionary containing:
            - lat: Latitude
            - lon: Longitude
            - display_name: Full formatted address
            - city: City name
            - country: Country name
        Returns None if address not found
    """
    # Respect rate limiting
    _respect_rate_limit()
    
    try:
        # Make request to Nominatim search API
        response = requests.get(
            f"{NOMINATIM_URL}/search",
            params={
                "q": address,
                "format": "json",
                "addressdetails": 1,
                "limit": 1
            },
            headers={"User-Agent": USER_AGENT},
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Check if any results found
        if not data:
            return None
        
        # Extract first result
        result = data[0]
        address_details = result.get("address", {})
        
        return {
            "lat": float(result["lat"]),
            "lon": float(result["lon"]),
            "display_name": result["display_name"],
            "city": address_details.get("city") or address_details.get("town") or address_details.get("village"),
            "country": address_details.get("country")
        }
    
    except requests.RequestException as error:
        print(f"Geocoding error: {error}")
        return None


def reverse_geocode(lat: float, lon: float) -> Optional[Dict]:
    """
    Convert GPS coordinates to address (reverse geocoding)
    
    Uses Nominatim API to find address for given coordinates.
    Returns structured address components.
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        Dictionary containing:
            - display_name: Full formatted address
            - city: City name
            - country: Country name
            - postcode: Postal code
            - road: Street/road name
        Returns None if location not found
    """
    # Respect rate limiting
    _respect_rate_limit()
    
    try:
        # Make request to Nominatim reverse API
        response = requests.get(
            f"{NOMINATIM_URL}/reverse",
            params={
                "lat": lat,
                "lon": lon,
                "format": "json",
                "addressdetails": 1
            },
            headers={"User-Agent": USER_AGENT},
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Check if valid response
        if "error" in data:
            return None
        
        address_details = data.get("address", {})
        
        return {
            "display_name": data.get("display_name"),
            "city": address_details.get("city") or address_details.get(" town") or address_details.get("village"),
            "country": address_details.get("country"),
            "postcode": address_details.get("postcode"),
            "road": address_details.get("road")
        }
    
    except requests.RequestException as error:
        print(f"Reverse geocoding error: {error}")
        return None
''')
    
    # File 3: telemetry.py
    with open("backend/telemetry.py", "w", encoding="utf-8") as f:
        f.write('''"""
Telemetry Processing Module
GeoEngine - Real-Time GPS Data Processing

This module handles GPS telemetry data from assets (vehicles, devices).
Processes incoming telemetry, classifies movement patterns,
and stores data for traffic analysis and ML training.

Detects movement types: MOVING, IDLE, SPEEDING
"""

from pydantic import BaseModel
from typing import Dict,List
from datetime import datetime

# Telemetry data model
class TelemetryData(BaseModel):
    """Pydantic model for telemetry data validation"""
    timestamp: str  # ISO 8601 format
    latitude: float
    longitude: float
    speed: float  # Speed in km/h
    asset_id: str  # Unique identifier for the asset

# In-memory storage for recent telemetry (for demo purposes)
# In production, this would be in a database
telemetry_store: Dict[str, List[Dict]]  = {}

# Speed thresholds for event classification
IDLE_THRESHOLD = 5  # km/h - below this is considered idle
SPEEDING_THRESHOLD = 80  # km/h - above this is considered speeding


def process_telemetry(data: TelemetryData) -> Dict:
    """
    Process incoming GPS telemetry data
    
    Validates data, classifies movement type, and stores for analysis.
    Updates traffic weights for routing engine.
    
    Args:
        data: TelemetryData object with timestamp, coordinates, speed, asset_id
    
    Returns:
        Dictionary containing:
            - status: "success"
            - event_type: "MOVING", "IDLE", or "SPEEDING"
            - asset_id: The asset identifier
            - recorded_count: Number of records for this asset
    """
    # Determine movement type based on speed
    if data.speed < IDLE_THRESHOLD:
        event_type = "IDLE"
    elif data.speed > SPEEDING_THRESHOLD:
        event_type = "SPEEDING"
    else:
        event_type = "MOVING"
    
    # Store telemetry data
    if data.asset_id not in telemetry_store:
        telemetry_store[data.asset_id] = []
    
    telemetry_record = {
        "timestamp": data.timestamp,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "speed": data.speed,
        "event_type": event_type
    }
    
    telemetry_store[data.asset_id].append(telemetry_record)
    
    # Keep only last 100 records per asset to avoid memory issues
    if len(telemetry_store[data.asset_id]) > 100:
        telemetry_store[data.asset_id] = telemetry_store[data.asset_id][-100:]
    
    print(f"Telemetry processed: Asset {data.asset_id}, Speed {data.speed} km/h, Type: {event_type}")
    
    return {
        "status": "success",
        "event_type": event_type,
        "asset_id": data.asset_id,
        "recorded_count": len(telemetry_store[data.asset_id])
    }


def get_recent_telemetry(asset_id: str = None, limit: int = 50) -> List[Dict]:
    """
    Retrieve recent telemetry data
    
    Args:
        asset_id: Optional asset ID to filter by
        limit: Maximum number of records to return
    
    Returns:
        List of telemetry records
    """
    if asset_id:
        # Return telemetry for specific asset
        return telemetry_store.get(asset_id, [])[-limit:]
    else:
        # Return telemetry for all assets
        all_telemetry = []
        for records in telemetry_store.values():
            all_telemetry.extend(records)
        
        # Sort by timestamp and return most recent
        all_telemetry.sort(key=lambda x: x["timestamp"], reverse=True)
        return all_telemetry[:limit]
''')
    
    print("✅ Backend feature files created successfully!")
    print("   - geofence.py (Bengaluru campuses)")
    print("   - geocoding.py (Nominatim API)")
    print("   - telemetry.py (GPS data processing)")

if __name__ == "__main__":
    create_files()
