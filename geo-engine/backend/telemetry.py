"""
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
