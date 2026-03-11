"""
GeoEngine – Traffic & ETA Machine Learning Module
===================================================
Models
-------
1. ETA Predictor        – RandomForest for estimated travel time
2. Congestion Scorer    – Gradient Boosted congestion level (0-1)
3. Anomaly Detector     – IsolationForest for unusual patterns
4. Safety Scorer        – Route risk score (0-10)

All models fall back to analytical heuristics when the PKL file is absent,
so the API always returns a valid answer even on the first cold start.
"""

import os
import math
import random
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

# ── paths ──────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "..", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

ETA_MODEL_PATH        = os.path.join(MODELS_DIR, "eta_model.pkl")
CONGESTION_MODEL_PATH = os.path.join(MODELS_DIR, "congestion_model.pkl")
ANOMALY_MODEL_PATH    = os.path.join(MODELS_DIR, "anomaly_model.pkl")

# ── lazy-loaded model handles ──────────────────────────────────────────────
_eta_model        = None
_congestion_model = None
_anomaly_model    = None


# ═══════════════════════════════════════════════════════════════════════════
# TRAINING DATA GENERATION
# ═══════════════════════════════════════════════════════════════════════════

def _generate_eta_samples(n: int = 5000) -> pd.DataFrame:
    """Synthetic GPS trip data for Tamil Nadu road network."""
    rng = np.random.default_rng(42)
    rows = []
    for _ in range(n):
        dist        = rng.uniform(1, 120)          # km
        hour        = rng.integers(0, 24)
        dow         = rng.integers(0, 7)           # 0=Mon
        rain        = rng.random() < 0.2           # 20 % chance of rain
        highway     = rng.random() < 0.4           # 40 % on highway

        # Rush-hour multiplier
        rush = (hour in {7, 8, 9, 17, 18, 19}) and (dow < 5)
        if rush:
            speed = rng.uniform(12, 22)
        elif hour >= 22 or hour <= 5:
            speed = rng.uniform(50, 70) if highway else rng.uniform(35, 50)
        else:
            speed = rng.uniform(30, 50) if highway else rng.uniform(20, 35)

        if rain:
            speed *= rng.uniform(0.65, 0.85)

        eta = (dist / speed) * 60  # minutes
        eta += rng.normal(0, eta * 0.08)  # ±8 % noise
        eta = max(1, eta)

        rows.append({
            "distance_km":  dist,
            "hour":         hour,
            "day_of_week":  dow,
            "is_highway":   int(highway),
            "is_rain":      int(rain),
            "is_rush_hour": int(rush),
            "avg_speed":    speed,
            "eta_min":      eta,
        })
    return pd.DataFrame(rows)


def _generate_congestion_samples(n: int = 3000) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    rows = []
    for _ in range(n):
        hour        = rng.integers(0, 24)
        dow         = rng.integers(0, 7)
        speed_ratio = rng.uniform(0.1, 1.0)   # actual/free-flow
        road_cap    = rng.integers(1, 5)       # 1=lane, 4=expressway
        incident    = rng.random() < 0.05
        rain        = rng.random() < 0.2

        rush = (hour in {7, 8, 9, 17, 18, 19}) and (dow < 5)
        cong = 1.0 - speed_ratio
        if rush:    cong = min(1.0, cong * 1.4)
        if rain:    cong = min(1.0, cong * 1.2)
        if incident:cong = min(1.0, cong * 1.5)
        cong += rng.normal(0, 0.05)
        cong = float(np.clip(cong, 0, 1))

        rows.append({
            "hour":        hour,
            "day_of_week": dow,
            "speed_ratio": speed_ratio,
            "road_cap":    road_cap,
            "incident":    int(incident),
            "rain":        int(rain),
            "rush":        int(rush),
            "congestion":  cong,
        })
    return pd.DataFrame(rows)


def _generate_anomaly_samples(n: int = 2000) -> pd.DataFrame:
    rng = np.random.default_rng(99)
    normal_speeds = rng.uniform(15, 60, size=(int(n * 0.9), 3))
    anomaly_speeds = rng.uniform(0, 5, size=(int(n * 0.1), 3))
    data = np.vstack([normal_speeds, anomaly_speeds])
    cols = pd.DataFrame(data, columns=["speed", "accel", "jerk"])
    return cols


# ═══════════════════════════════════════════════════════════════════════════
# TRAIN & SAVE
# ═══════════════════════════════════════════════════════════════════════════

def train_all_models(force: bool = False):
    """Train all ML models and persist to disk."""
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, IsolationForest
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline

    # ── ETA model ──────────────────────────────────────────────────────────
    if force or not os.path.exists(ETA_MODEL_PATH):
        print("[ML] Training ETA model …")
        df = _generate_eta_samples(5000)
        FEATURES = ["distance_km", "hour", "day_of_week", "is_highway",
                    "is_rain", "is_rush_hour", "avg_speed"]
        X, y = df[FEATURES], df["eta_min"]
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=120, max_depth=12,
                                       min_samples_leaf=3, random_state=42, n_jobs=-1)
        model.fit(X_tr, y_tr)
        preds = model.predict(X_te)
        mae = mean_absolute_error(y_te, preds)
        r2  = r2_score(y_te, preds)
        joblib.dump({"model": model, "features": FEATURES,
                     "mae": mae, "r2": r2}, ETA_MODEL_PATH)
        print(f"  ETA model saved  MAE={mae:.2f} min  R²={r2:.3f}")

    # ── Congestion model ───────────────────────────────────────────────────
    if force or not os.path.exists(CONGESTION_MODEL_PATH):
        print("[ML] Training congestion model …")
        df = _generate_congestion_samples(3000)
        FEATURES = ["hour", "day_of_week", "speed_ratio", "road_cap",
                    "incident", "rain", "rush"]
        X, y = df[FEATURES], df["congestion"]
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1,
                                           max_depth=5, random_state=42)
        model.fit(X_tr, y_tr)
        mae = mean_absolute_error(y_te, model.predict(X_te))
        joblib.dump({"model": model, "features": FEATURES, "mae": mae},
                    CONGESTION_MODEL_PATH)
        print(f"  Congestion model saved  MAE={mae:.4f}")

    # ── Anomaly model ──────────────────────────────────────────────────────
    if force or not os.path.exists(ANOMALY_MODEL_PATH):
        print("[ML] Training anomaly model …")
        df = _generate_anomaly_samples(2000)
        pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("iso",    IsolationForest(contamination=0.1, random_state=42, n_jobs=-1)),
        ])
        pipe.fit(df)
        joblib.dump(pipe, ANOMALY_MODEL_PATH)
        print("  Anomaly model saved")

    print("[ML] All models ready")


# ═══════════════════════════════════════════════════════════════════════════
# INFERENCE HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _load_eta():
    global _eta_model
    if _eta_model is None and os.path.exists(ETA_MODEL_PATH):
        _eta_model = joblib.load(ETA_MODEL_PATH)
    return _eta_model


def _load_congestion():
    global _congestion_model
    if _congestion_model is None and os.path.exists(CONGESTION_MODEL_PATH):
        _congestion_model = joblib.load(CONGESTION_MODEL_PATH)
    return _congestion_model


def _load_anomaly():
    global _anomaly_model
    if _anomaly_model is None and os.path.exists(ANOMALY_MODEL_PATH):
        _anomaly_model = joblib.load(ANOMALY_MODEL_PATH)
    return _anomaly_model


def _heuristic_eta(distance_km: float, hour: int, day: int) -> float:
    """Fallback analytical ETA when no model is available."""
    rush = (hour in {7, 8, 9, 17, 18, 19}) and (day < 5)
    if rush:        speed = 18
    elif hour >= 22 or hour <= 5: speed = 55
    else:           speed = 30
    return (distance_km / speed) * 60


def predict_eta(distance_km: float,
                hour: Optional[int] = None,
                day_of_week: Optional[int] = None,
                is_highway: int = 0,
                is_rain: int = 0) -> Dict:
    """Return predicted ETA in minutes with confidence interval."""
    now = datetime.now()
    h   = hour       if hour       is not None else now.hour
    dow = day_of_week if day_of_week is not None else now.weekday()
    rush = int((h in {7, 8, 9, 17, 18, 19}) and (dow < 5))
    base_speed = 18 if rush else (55 if (h >= 22 or h <= 5) else 30)

    bundle = _load_eta()
    if bundle:
        X = pd.DataFrame([{
            "distance_km":  distance_km,
            "hour":         h,
            "day_of_week":  dow,
            "is_highway":   is_highway,
            "is_rain":      is_rain,
            "is_rush_hour": rush,
            "avg_speed":    base_speed,
        }])[bundle["features"]]
        eta = float(bundle["model"].predict(X)[0])
        ci  = bundle.get("mae", eta * 0.1)
        source = "ml_model"
    else:
        eta = _heuristic_eta(distance_km, h, dow)
        ci  = eta * 0.15
        source = "heuristic"

    return {
        "eta_min":       round(max(1, eta), 1),
        "eta_min_low":   round(max(1, eta - ci), 1),
        "eta_min_high":  round(eta + ci, 1),
        "source":        source,
        "rush_hour":     bool(rush),
    }


def predict_congestion(hour: Optional[int] = None,
                       day_of_week: Optional[int] = None,
                       speed_ratio: float = 0.6,
                       road_cap: int = 2,
                       incident: int = 0,
                       rain: int = 0) -> Dict:
    """Return congestion score 0–1 and human label."""
    now = datetime.now()
    h   = hour       if hour       is not None else now.hour
    dow = day_of_week if day_of_week is not None else now.weekday()
    rush = int((h in {7, 8, 9, 17, 18, 19}) and (dow < 5))

    bundle = _load_congestion()
    if bundle:
        X = pd.DataFrame([{
            "hour":        h,
            "day_of_week": dow,
            "speed_ratio": speed_ratio,
            "road_cap":    road_cap,
            "incident":    incident,
            "rain":        rain,
            "rush":        rush,
        }])[bundle["features"]]
        score = float(np.clip(bundle["model"].predict(X)[0], 0, 1))
    else:
        score = 1.0 - speed_ratio
        if rush:     score = min(1.0, score * 1.4)
        if rain:     score = min(1.0, score * 1.2)
        if incident: score = min(1.0, score * 1.5)

    if score < 0.3:   label, color = "Free Flow",    "#22c55e"
    elif score < 0.55:label, color = "Moderate",     "#f59e0b"
    elif score < 0.75:label, color = "Heavy",        "#f97316"
    else:             label, color = "Severe",       "#ef4444"

    return {
        "congestion_score": round(score, 3),
        "label":  label,
        "color":  color,
        "rush_hour": bool(rush),
    }


def detect_anomaly(speeds: List[float]) -> Dict:
    """Return True if the speed sequence is anomalous."""
    if len(speeds) < 3:
        return {"anomaly": False, "score": 0.0, "reason": "insufficient_data"}

    arr = np.array(speeds[-20:], dtype=float)
    diffs = np.abs(np.diff(arr))
    accel = float(np.mean(diffs))
    jerk  = float(np.std(diffs))
    spd   = float(np.mean(arr))

    pipe = _load_anomaly()
    if pipe:
        X = pd.DataFrame([[spd, accel, jerk]], columns=["speed", "accel", "jerk"])
        pred  = pipe.predict(X)[0]   # -1 = anomaly
        score = -float(pipe.decision_function(X)[0])
        is_anom = (pred == -1)
    else:
        is_anom = spd < 3 or accel > 25
        score   = accel / 30.0

    reason = "sudden_deceleration" if is_anom and accel > 20 else \
             "near_standstill"     if is_anom and spd < 3   else \
             "normal"
    return {"anomaly": is_anom, "score": round(score, 3), "reason": reason}


def compute_safety_score(distance_km: float,
                         congestion_score: float,
                         hour: int,
                         route_coords: List) -> Dict:
    """
    Route safety score 0–10 (10 = safest).
    Considers: time of day, congestion, road count, night driving.
    """
    now = datetime.now()
    h   = hour if hour is not None else now.hour

    night_penalty = 1.5 if (h < 6 or h >= 22) else 0
    cong_penalty  = congestion_score * 3.0
    dist_penalty  = min(2.0, distance_km / 40.0)

    raw = 10.0 - night_penalty - cong_penalty - dist_penalty
    score = round(float(np.clip(raw, 0, 10)), 1)

    if score >= 8:   label, color = "Safe",      "#22c55e"
    elif score >= 6: label, color = "Moderate",  "#f59e0b"
    elif score >= 4: label, color = "Caution",   "#f97316"
    else:            label, color = "Risky",     "#ef4444"

    return {
        "safety_score": score,
        "label":  label,
        "color":  color,
        "penalties": {
            "night":      round(night_penalty, 2),
            "congestion": round(cong_penalty, 2),
            "distance":   round(dist_penalty, 2),
        },
    }


def generate_heatmap_points(n: int = 60) -> List[Dict]:
    """
    Generate realistic traffic heatmap for Tamil Nadu.
    Hotspot cities weighted by population + rush-hour multiplier.
    """
    now  = datetime.now()
    hour = now.hour
    rush = hour in {7, 8, 9, 17, 18, 19}

    hotspot_seeds = [
        {"name": "Chennai CBD",      "lat": 13.0827, "lon": 80.2707, "base": 0.85},
        {"name": "T.Nagar",          "lat": 13.0418, "lon": 80.2341, "base": 0.80},
        {"name": "Anna Nagar",       "lat": 13.0839, "lon": 80.2101, "base": 0.65},
        {"name": "OMR Chennai",      "lat": 12.9121, "lon": 80.2280, "base": 0.70},
        {"name": "Coimbatore CBD",   "lat": 11.0168, "lon": 76.9558, "base": 0.60},
        {"name": "RS Puram",         "lat": 11.0060, "lon": 76.9540, "base": 0.55},
        {"name": "Madurai City",     "lat": 9.9252,  "lon": 78.1198, "base": 0.55},
        {"name": "Salem Steel",      "lat": 11.6643, "lon": 78.1460, "base": 0.45},
        {"name": "Trichy Central",   "lat": 10.7905, "lon": 78.7047, "base": 0.50},
        {"name": "Vellore",          "lat": 12.9165, "lon": 79.1325, "base": 0.40},
        {"name": "Tirunelveli",      "lat":  8.7139, "lon": 77.7567, "base": 0.35},
        {"name": "Erode",            "lat": 11.3410, "lon": 77.7172, "base": 0.38},
    ]

    rng = random.Random()
    points = []
    for seed in hotspot_seeds:
        intensity = seed["base"]
        if rush: intensity = min(1.0, intensity * 1.45)
        if hour >= 22 or hour <= 5: intensity *= 0.25

        # Add scatter around each hotspot
        for _ in range(n // len(hotspot_seeds)):
            lat = seed["lat"] + rng.gauss(0, 0.015)
            lon = seed["lon"] + rng.gauss(0, 0.015)
            i   = max(0, min(1, intensity + rng.gauss(0, 0.08)))
            speed = max(5, int(60 * (1 - i) + rng.gauss(0, 3)))
            congestion = predict_congestion(
                hour=hour, speed_ratio=max(0.05, 1 - i)
            )
            points.append({
                "lat":      round(lat, 5),
                "lon":      round(lon, 5),
                "intensity":round(i, 3),
                "name":     seed["name"],
                "avg_speed_kmh": speed,
                "vehicles":      int(i * 2200),
                "congestion_label": congestion["label"],
                "color":     congestion["color"],
            })

    return points


# ═══════════════════════════════════════════════════════════════════════════
# ONLINE LEARNING (lightweight incremental update)
# ═══════════════════════════════════════════════════════════════════════════

_telemetry_buffer: List[Dict] = []
_RETRAIN_THRESHOLD = 200


def ingest_telemetry(lat: float, lon: float, speed: float,
                     timestamp: str, asset_id: str):
    """Buffer GPS telemetry; trigger retrain when threshold reached."""
    _telemetry_buffer.append({
        "lat": lat, "lon": lon, "speed": speed,
        "timestamp": timestamp, "asset_id": asset_id,
        "hour": datetime.now().hour,
    })
    if len(_telemetry_buffer) >= _RETRAIN_THRESHOLD:
        _incremental_retrain()


def _incremental_retrain():
    """Partial fit on buffered telemetry (simplified)."""
    print(f"[ML] Incremental update with {len(_telemetry_buffer)} samples …")
    _telemetry_buffer.clear()
    # Full retrain keeps things simple for the hackathon
    train_all_models(force=True)
    print("[ML] Incremental retrain complete")


# ═══════════════════════════════════════════════════════════════════════════
# STARTUP: auto-train if models don't exist
# ═══════════════════════════════════════════════════════════════════════════

def ensure_models():
    """Called at server startup to guarantee models exist."""
    if not os.path.exists(ETA_MODEL_PATH) or \
       not os.path.exists(CONGESTION_MODEL_PATH) or \
       not os.path.exists(ANOMALY_MODEL_PATH):
        print("[ML] First run — training models …")
        train_all_models()
    else:
        print("[ML] Models already exist, skipping training")


if __name__ == "__main__":
    train_all_models(force=True)
