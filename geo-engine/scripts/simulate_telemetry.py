"""
GPS Telemetry Simulator
GeoEngine - Bengaluru, India

This script simulates 5 GPS assets moving around Bengaluru.
Sends real-time telemetry data to the backend API for testing and demonstration.

Features:
- Simulates 5 assets with unique IDs
- Generates realistic GPS movement (small increments)
- Varying speeds (10-60 km/h)
- Sends POST requests to /telemetry endpoint every 1 second
- Console output for each telemetry event
"""

import requests
import time
import random
from datetime import datetime
import json

# Backend API URL
API_URL = "http://localhost:8000/telemetry"

# Bengaluru center coordinates
BENGALURU_CENTER = (12.9716, 77.5946)

# Initialize 5 assets with random starting positions near Bengaluru
assets = []
for asset_num in range(1, 6):
    assets.append({
        "id": f"ASSET-{asset_num:03d}",
        "lat": BENGALURU_CENTER[0] + (random.random() - 0.5) * 0.05,
        "lon": BENGALURU_CENTER[1] + (random.random() - 0.5) * 0.05,
        "speed": random.uniform(20, 40)  # Initial speed in km/h
    })


def generate_movement(asset):
    """
    Generate realistic GPS movement for an asset
    
    Updates latitude, longitude, and speed with small random increments.
    Simulates natural vehicle movement patterns.
    """
    # Small random movement (approximately 50-200 meters)
    delta_lat = (random.random() - 0.5) * 0.003
    delta_lon = (random.random() - 0.5) * 0.003
    
    asset["lat"] += delta_lat
    asset["lon"] += delta_lon
    
    # Vary speed realistically (±10 km/h change)
    asset["speed"] += (random.random() - 0.5) * 10
    
    # Keep speed within realistic bounds
    asset["speed"] = max(5, min(60, asset["speed"]))
    
    # Occasionally stop (simulate traffic lights, etc.)
    if random.random() < 0.1:  # 10% chance
        asset["speed"] = random.uniform(0, 5)


def send_telemetry(asset):
    """
    Send telemetry data to the backend API
    
    Makes POST request to /telemetry endpoint with GPS data.
    Prints status to console.
    """
    telemetry_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "latitude": asset["lat"],
        "longitude": asset["lon"],
        "speed": round(asset["speed"], 2),
        "asset_id": asset["id"]
    }
    
    try:
        response = requests.post(API_URL, json=telemetry_data, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            event_type = result.get("event_type", "UNKNOWN")
            
            # Color-coded console output
            color_code = {
                "MOVING": "\033[92m",  # Green
                "IDLE": "\033[93m",     # Yellow
                "SPEEDING": "\033[91m"  # Red
            }.get(event_type, "\033[0m")
            
            print(f"{color_code}[{asset['id']}] "
                  f"Lat:{asset['lat']:.4f} Lon:{asset['lon']:.4f} "
                  f"Speed:{asset['speed']:.1f} km/h "
                  f"→ {event_type}\033[0m")
        else:
            print(f"[{asset['id']}] ❌ Error: HTTP {response.status_code}")
    
    except requests.RequestException as error:
        print(f"[{asset['id']}] ❌ Connection error: {error}")


def main():
    """
    Main simulation loop
    
    Continuously simulates GPS movement and sends telemetry data.
    Runs indefinitely until interrupted with Ctrl+C.
    """
    print("="*60)
    print("GPS TELEMETRY SIMULATOR")
    print("GeoEngine - Bengaluru, India")
    print("="*60)
    print(f"\nSimulating {len(assets)} assets...")
    print(f"Sending telemetry to: {API_URL}")
    print("\nPress Ctrl+C to stop\n")
    print("="*60)
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            print(f"\n📡 Iteration {iteration} - {datetime.now().strftime('%H:%M:%S')}")
            print("-"*60)
            
            # Process each asset
            for asset in assets:
                # Generate new position and speed
                generate_movement(asset)
                
                # Send telemetry to backend
                send_telemetry(asset)
                
                # Small delay between assets to avoid overwhelming the server
                time.sleep(0.1)
            
            # Wait 1 second before next iteration
            time.sleep(0.9)
    
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("Simulation stopped by user")
        print(f"Total iterations: {iteration}")
        print("="*60)


if __name__ == "__main__":
    main()
