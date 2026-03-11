"""
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
