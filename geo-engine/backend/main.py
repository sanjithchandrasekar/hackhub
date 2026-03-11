"""
GeoEngine – Intelligent Geospatial Engine with Real-Time Learning
=================================================================
FastAPI backend  |  Version 3.0  |  Tamil Nadu, India

Endpoints
---------
  POST /route                 – single best route
  POST /multi-route           – 3 alternatives with safety scores
  POST /geofence-check        – point-in-polygon + entry/exit events
  POST /geocode               – address → lat/lon
  POST /reverse-geocode       – lat/lon → address
  GET  /traffic-heatmap       – ML-driven congestion heatmap
  GET  /nearby-places         – POIs near a coordinate
  POST /telemetry             – ingest live GPS + online learning
  GET  /analytics/routes      – dashboard stats
  GET  /analytics/ml          – model performance metrics
  GET  /health                – health-check
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import math
import random
from datetime import datetime

# ── local modules ──────────────────────────────────────────────────────────
from routing   import compute_route, compute_alternative_routes
from geofence  import check_geofence, get_all_campuses
from geocoding import forward_geocode, reverse_geocode, search_nearby_poi
from telemetry import process_telemetry, TelemetryData, get_all_assets_live
from ml_model  import (
    ensure_models,
    predict_eta,
    predict_congestion,
    detect_anomaly,
    compute_safety_score,
    generate_heatmap_points,
    ingest_telemetry,
    train_all_models,
)

# ── startup: guarantee ML models exist ────────────────────────────────────
print("[boot] Ensuring ML models …")
ensure_models()

# ── app ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="GeoEngine API",
    description="Intelligent Geospatial Engine with Real-Time Learning",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── in-memory stores ───────────────────────────────────────────────────────
route_history:    List[Dict] = []
geofence_events:  List[Dict] = []
anomaly_log:      List[Dict] = []
asset_speeds:     Dict[str, List[float]] = {}


# ════════════════════════════════════════════════════════════════════════════
# REQUEST MODELS
# ════════════════════════════════════════════════════════════════════════════

class RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat:   float
    end_lon:   float
    mode:      Optional[str] = "fastest"   # fastest | shortest | balanced

class MultiRouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat:   float
    end_lon:   float

class GeofenceRequest(BaseModel):
    lat:      float
    lon:      float
    asset_id: Optional[str] = "user"

class GeocodeRequest(BaseModel):
    address: str

class ReverseGeocodeRequest(BaseModel):
    lat: float
    lon: float

class NearbyRequest(BaseModel):
    lat:       float
    lon:       float
    radius_km: Optional[float] = 2.0
    category:  Optional[str]   = "all"

class ETARequest(BaseModel):
    distance_km: float
    hour:        Optional[int] = None
    is_highway:  Optional[int] = 0
    is_rain:     Optional[int] = 0


# ════════════════════════════════════════════════════════════════════════════
# UTILITY
# ════════════════════════════════════════════════════════════════════════════

def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    a = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def _save_route(result: Dict, mode: str):
    route_history.append({**result, "timestamp": datetime.now().isoformat(), "mode": mode})
    if len(route_history) > 100:
        route_history.pop(0)


# ════════════════════════════════════════════════════════════════════════════
# CORE ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {"status": "online", "service": "GeoEngine", "version": "3.0.0",
            "docs": "/docs", "region": "Tamil Nadu, India"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "3.0.0",
        "routes_computed": len(route_history),
        "geofence_events": len(geofence_events),
        "anomalies_detected": len(anomaly_log),
        "timestamp": datetime.now().isoformat(),
    }


# ── Route endpoints ────────────────────────────────────────────────────────

@app.post("/route")
async def calculate_route(req: RouteRequest):
    """Best single route with ML-predicted ETA and safety score."""
    try:
        result = compute_route(req.start_lat, req.start_lon,
                               req.end_lat,   req.end_lon, mode=req.mode)

        # ML enrichment
        eta_pred  = predict_eta(result["distance_km"])
        cong_pred = predict_congestion()
        safety    = compute_safety_score(
            result["distance_km"],
            cong_pred["congestion_score"],
            datetime.now().hour,
            result.get("route", []),
        )

        result["eta_ml"]        = eta_pred
        result["congestion"]    = cong_pred
        result["safety"]        = safety
        result["estimated_time_min"] = eta_pred["eta_min"]

        _save_route(result, req.mode)
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/multi-route")
async def multi_route(req: MultiRouteRequest):
    """3 alternative routes (fastest / shortest / balanced) with ML scores."""
    try:
        routes = compute_alternative_routes(
            req.start_lat, req.start_lon, req.end_lat, req.end_lon
        )

        now = datetime.now()
        enriched = []
        for r in routes:
            eta_pred = predict_eta(r["distance_km"])
            cong     = predict_congestion()
            safety   = compute_safety_score(
                r["distance_km"], cong["congestion_score"], now.hour, r.get("route", [])
            )
            r["eta_ml"]     = eta_pred
            r["congestion"] = cong
            r["safety"]     = safety
            r["estimated_time_min"] = eta_pred["eta_min"]
            enriched.append(r)

        # Sort by safety score descending (safest first)
        enriched.sort(key=lambda x: x["safety"]["safety_score"], reverse=True)
        return {"status": "success", "routes": enriched, "count": len(enriched)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Geofence ───────────────────────────────────────────────────────────────

@app.get("/geofence")
async def list_geofences():
    return {"status": "success", "campuses": get_all_campuses()}

@app.post("/geofence-check")
async def geofence_check(req: GeofenceRequest):
    """Check if coordinate is inside a campus and emit entry/exit events."""
    try:
        result = check_geofence(req.lat, req.lon, req.asset_id)

        if result.get("event") in ("ENTRY", "EXIT"):
            event = {
                "asset_id":  req.asset_id,
                "campus":    result.get("campus"),
                "event":     result["event"],
                "lat":       req.lat,
                "lon":       req.lon,
                "timestamp": datetime.now().isoformat(),
            }
            geofence_events.append(event)
            if len(geofence_events) > 200:
                geofence_events.pop(0)

        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# keep legacy path working
@app.post("/geofence")
async def geofence_legacy(req: GeofenceRequest):
    return await geofence_check(req)

@app.get("/geofence/events")
async def get_geofence_events(limit: int = Query(50, le=200)):
    return {"status": "success", "events": geofence_events[-limit:],
            "total": len(geofence_events)}


# ── Geocoding ──────────────────────────────────────────────────────────────

@app.post("/geocode")
async def geocode(req: GeocodeRequest):
    try:
        return {"status": "success", **forward_geocode(req.address)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reverse-geocode")
async def rev_geocode(req: ReverseGeocodeRequest):
    try:
        return {"status": "success", **reverse_geocode(req.lat, req.lon)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Nearby places ──────────────────────────────────────────────────────────

@app.get("/nearby-places")
async def nearby_places_get(
    lat:       float = Query(...),
    lon:       float = Query(...),
    radius_km: float = Query(2.0),
    category:  str   = Query("all"),
):
    try:
        pois = search_nearby_poi(lat, lon, radius_km, category)
        return {"status": "success", "pois": pois, "count": len(pois)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/nearby-places")
async def nearby_places_post(req: NearbyRequest):
    try:
        pois = search_nearby_poi(req.lat, req.lon, req.radius_km, req.category)
        return {"status": "success", "pois": pois, "count": len(pois)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# legacy alias
@app.post("/poi/search")
async def poi_search(req: NearbyRequest):
    return await nearby_places_post(req)


# ── Traffic heatmap ────────────────────────────────────────────────────────

@app.get("/traffic-heatmap")
async def traffic_heatmap(points: int = Query(60, le=200)):
    """ML-generated traffic heatmap for Tamil Nadu."""
    try:
        hotspots = generate_heatmap_points(points)
        return {
            "status":    "success",
            "hotspots":  hotspots,
            "count":     len(hotspots),
            "timestamp": datetime.now().isoformat(),
            "rush_hour": datetime.now().hour in {7, 8, 9, 17, 18, 19},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# legacy alias
@app.get("/traffic/heatmap")
async def traffic_heatmap_legacy():
    return await traffic_heatmap()


# ── ML prediction endpoints ────────────────────────────────────────────────

@app.post("/predict/eta")
async def predict_eta_endpoint(req: ETARequest):
    """Standalone ML ETA prediction."""
    try:
        result = predict_eta(
            req.distance_km,
            hour=req.hour,
            is_highway=req.is_highway,
            is_rain=req.is_rain,
        )
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predict/congestion")
async def predict_congestion_endpoint(
    hour: Optional[int] = None,
    speed_ratio: float  = Query(0.6, ge=0, le=1),
):
    try:
        return {"status": "success", **predict_congestion(hour=hour, speed_ratio=speed_ratio)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Telemetry & online learning ───────────────────────────────────────────

@app.post("/telemetry")
async def telemetry(data: TelemetryData):
    try:
        result = process_telemetry(data)

        # Anomaly detection per asset
        aid = data.asset_id
        if aid not in asset_speeds:
            asset_speeds[aid] = []
        asset_speeds[aid].append(data.speed)
        if len(asset_speeds[aid]) > 50:
            asset_speeds[aid] = asset_speeds[aid][-50:]

        anom = detect_anomaly(asset_speeds[aid])
        if anom["anomaly"]:
            anomaly_log.append({
                "asset_id":  aid,
                "reason":    anom["reason"],
                "score":     anom["score"],
                "lat":       data.latitude,
                "lon":       data.longitude,
                "speed":     data.speed,
                "timestamp": data.timestamp,
            })
            if len(anomaly_log) > 500:
                anomaly_log.pop(0)

        # Feed into online learning buffer
        ingest_telemetry(data.latitude, data.longitude, data.speed,
                         data.timestamp, data.asset_id)

        return {"status": "success", **result, "anomaly": anom}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/assets/live")
async def live_assets():
    try:
        assets = get_all_assets_live()
        return {"status": "success", "assets": assets, "count": len(assets)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/anomalies")
async def get_anomalies(limit: int = Query(20, le=100)):
    return {"status": "success", "anomalies": anomaly_log[-limit:],
            "total": len(anomaly_log)}


# ── ML retraining ─────────────────────────────────────────────────────────

@app.post("/ml/retrain")
async def retrain_models():
    """Trigger full model retrain (async-safe for hackathon)."""
    try:
        train_all_models(force=True)
        return {"status": "success", "message": "Models retrained successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Analytics ─────────────────────────────────────────────────────────────

@app.get("/analytics/routes")
async def analytics_routes():
    n = len(route_history)
    if n == 0:
        return {"status": "success", "total_routes": 0, "avg_distance_km": 0,
                "avg_time_min": 0, "recent_routes": []}
    avg_dist = sum(r.get("distance_km", 0) for r in route_history) / n
    avg_time = sum(r.get("estimated_time_min", 0) for r in route_history) / n
    mode_counts: Dict[str, int] = {}
    for r in route_history:
        m = r.get("mode", "fastest")
        mode_counts[m] = mode_counts.get(m, 0) + 1

    return {
        "status":          "success",
        "total_routes":    n,
        "avg_distance_km": round(avg_dist, 2),
        "avg_time_min":    round(avg_time, 2),
        "mode_breakdown":  mode_counts,
        "recent_routes":   route_history[-10:],
    }

@app.get("/analytics/ml")
async def analytics_ml():
    """Return ML model performance stats."""
    try:
        import joblib, os
        stats = {}
        for name, file_name in [
            ("eta",        "eta_model.pkl"),
            ("congestion", "congestion_model.pkl"),
        ]:
            path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "models", file_name)
            if os.path.exists(path):
                bundle = joblib.load(path)
                stats[name] = {
                    "mae":      round(bundle.get("mae", 0), 4),
                    "r2":       round(bundle.get("r2", 0), 4) if "r2" in bundle else None,
                    "features": bundle.get("features", []),
                }
        return {"status": "success", "models": stats,
                "anomaly_buffer_size": len(anomaly_log)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/geofence")
async def analytics_geofence():
    total   = len(geofence_events)
    entries = sum(1 for e in geofence_events if e["event"] == "ENTRY")
    exits   = sum(1 for e in geofence_events if e["event"] == "EXIT")
    campus_counts: Dict[str, int] = {}
    for e in geofence_events:
        c = e.get("campus", "unknown")
        campus_counts[c] = campus_counts.get(c, 0) + 1
    return {"status": "success", "total_events": total, "entries": entries,
            "exits": exits, "by_campus": campus_counts,
            "recent": geofence_events[-10:]}


# ════════════════════════════════════════════════════════════════════════════
# SERVER ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("\n" + "=" * 60)
    print("  GeoEngine  –  Intelligent Geospatial Engine v3.0")
    print("=" * 60)
    print("  Region  : Tamil Nadu, India")
    print("  Server  : http://localhost:8000")
    print("  API Docs: http://localhost:8000/docs")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")



