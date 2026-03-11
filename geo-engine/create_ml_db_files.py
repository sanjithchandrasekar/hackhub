"""
Create ML and Database Backend Files for GeoEngine
"""

import os

def create_files():
    """Create retrain.py and database.py"""
    
    os.makedirs("backend", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    
    # File 1: retrain.py
    with open("backend/retrain.py", "w", encoding="utf-8") as f:
        f.write('''"""
ML Retraining Pipeline
GeoEngine - Real-Time Learning

This module implements the machine learning retraining pipeline.
Downloads fresh OSM data, generates synthetic training data,
trains a RandomForestRegressor for ETA prediction.

The model predicts estimated travel time based on:
- Distance
- Time of day
- Day of week
- Historical traffic patterns
"""

import osmnx as ox
import networkx as nx
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os
from datetime import datetime

# Configuration
BENGALURU_CENTER = (12.9716, 77.5946)
BENGALURU_DIST = 15000
MODEL_PATH = "models/eta_model.pkl"


def _generate_training_data(num_samples: int = 1000) -> pd.DataFrame:
    """
    Generate synthetic training data for ETA prediction
    
    Creates realistic training data based on distance, time, and traffic patterns.
    In production, this would use real historical telemetry data.
    
    Returns:
        Pandas DataFrame with features and target variable
    """
    print(f"Generating {num_samples} training samples...")
    
    np.random.seed(42)  # For reproducibility
    
    data = []
    for _ in range(num_samples):
        # Generate random trip characteristics
        distance_km = np.random.uniform(1, 25)  # 1-25 km trips
        hour_of_day = np.random.randint(0, 24)
        day_of_week = np.random.randint(0, 7)  # 0=Monday, 6=Sunday
        
        # Base speed varies by time of day (rush hour vs off-peak)
        if hour_of_day in [8, 9, 17, 18, 19]:  # Rush hours
            base_speed = np.random.uniform(15, 25)  # km/h
        elif hour_of_day >= 22 or hour_of_day <= 5:  # Night time
            base_speed = np.random.uniform(40, 50)
        else:  # Regular hours
            base_speed = np.random.uniform(25, 35)
        
        # Weekend modifier (less traffic)
        if day_of_week >= 5:  # Weekend
            base_speed *= 1.2
        
        # Calculate ETA in minutes
        eta_minutes = (distance_km / base_speed) * 60
        
        # Add some random noise
        eta_minutes += np.random.normal(0, 2)  # ±2 minutes noise
        
        data.append({
            "distance_km": distance_km,
            "hour_of_day": hour_of_day,
            "day_of_week": day_of_week,
            "eta_minutes": max(eta_minutes, 1)  # Ensure positive ETA
        })
    
    df = pd.DataFrame(data)
    print(f"Training data generated: {len(df)} samples")
    return df


def download_fresh_osm_data():
    """
    Download fresh OpenStreetMap data for Bengaluru
    
    This updates the road network with latest OSM data.
    Should be called periodically (e.g., weekly) for map updates.
    """
    print("Downloading fresh OSM data...")
    
    try:
        graph = ox.graph_from_point(
            BENGALURU_CENTER,
            dist=BENGALURU_DIST,
            network_type='drive',
            simplify=True
        )
        
        # Cache the updated graph
        cache_path = "../data/osm_data/bengaluru_network.pkl"
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        
        import pickle
        with open(cache_path, 'wb') as f:
            pickle.dump(graph, f)
        
        print(f"✅ OSM data updated: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
        return True
    
    except Exception as error:
        print(f"❌ OSM download failed: {error}")
        return False


def retrain_model():
    """
    Train or retrain the ETA prediction model
    
    1. Generates synthetic training data
    2. Trains RandomForestRegressor
    3. Evaluates model performance
    4. Saves model to disk
    
    Returns:
        Dictionary with training metrics
    """
    print("\\n" + "="*50)
    print("ML RETRAINING PIPELINE")
    print("="*50)
    
    # Generate training data
    df = _generate_training_data(num_samples=2000)
    
    # Prepare features and target
    X = df[["distance_km", "hour_of_day", "day_of_week"]]
    y = df["eta_minutes"]
    
    # Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"\\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Train Random Forest model
    print("\\nTraining RandomForestRegressor...")
    model = RandomForestRegressor(
        n_estimators=100,  # 100 decision trees
        max_depth=10,
        random_state=42,
        n_jobs=-1  # Use all CPU cores
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate model
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"\n📊 Model Performance:")
    print(f"   Mean Absolute Error: {mae:.2f} minutes")
    print(f"   R² Score: {r2:.4f}")
    print(f"   Feature Importances:")
    for feature_name, importance in zip(X.columns, model.feature_importances_):
        print(f"      {feature_name}: {importance:.3f}")
    
    # Save model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\n✅ Model saved to {MODEL_PATH}")
    
    return {
        "mae": round(mae, 2),
        "r2_score": round(r2, 4),
        "samples_trained": len(X_train),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Run the retraining pipeline
    print("Starting retraining pipeline...\\n")
    
    # Step 1: Download fresh OSM data (optional)
    # download_fresh_osm_data()
    
    # Step 2: Retrain the model
    metrics = retrain_model()
    
    print(f"\\n{'='*50}")
    print("RETRAINING COMPLETE")
    print(f"{'='*50}")
    print(f"Timestamp: {metrics['timestamp']}")
    print(f"MAE: {metrics['mae']} min")
    print(f"R²: {metrics['r2_score']}")
''')
    
    # File 2: database.py
    with open("backend/database.py", "w", encoding="utf-8") as f:
        f.write('''"""
Database Module
GeoEngine - Data Persistence Layer

This module handles database operations for storing:
- Route calculations
- Telemetry logs
- Training data for ML

Supports both PostgreSQL (production) and SQLite (local development).
Falls back to SQLite if PostgreSQL is not available.
"""

import os
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Get database URL from environment or use SQLite as fallback
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./geo_engine.db")

# SQLAlchemy setup
Base = declarative_base()


# ============ TABLE MODELS ============

class Route(Base):
    """Table for storing calculated routes"""
    __tablename__ = "routes"
    
    id = Column(Integer, primary_key=True, index=True)
    start_lat = Column(Float, nullable=False)
    start_lon = Column(Float, nullable=False)
    end_lat = Column(Float, nullable=False)
    end_lon = Column(Float, nullable=False)
    distance_km = Column(Float, nullable=False)
    eta_min = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TelemetryLog(Base):
    """Table for storing GPS telemetry data"""
    __tablename__ = "telemetry_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String, index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    event_type = Column(String)  # MOVING, IDLE, SPEEDING


# ============ DATABASE CONNECTION ============

# Create engine
try:
    if "postgresql" in DATABASE_URL:
        # PostgreSQL connection
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        logger.info("Connected to PostgreSQL database")
    else:
        # SQLite connection
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False}  # SQLite specific
        )
        logger.info("Using SQLite database")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    logger.info("Database tables created successfully")

except Exception as error:
    logger.error(f"Database connection error: {error}")
    # Create a fallback SQLite database
    fallback_url = "sqlite:///./geo_engine_fallback.db"
    engine = create_engine(fallback_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.warning(f"Using fallback SQLite database: {fallback_url}")


# ============ DATABASE OPERATIONS ============

def save_route(start_lat: float, start_lon: float, 
               end_lat: float, end_lon: float,
               distance_km: float, eta_min: float) -> int:
    """
    Save calculated route to database
    
    Args:
        start_lat, start_lon: Starting coordinates
        end_lat, end_lon: Ending coordinates
        distance_km: Route distance in kilometers
        eta_min: Estimated time in minutes
    
    Returns:
        Route ID
    """
    db = SessionLocal()
    try:
        route = Route(
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon,
            distance_km=distance_km,
            eta_min=eta_min
        )
        
        db.add(route)
        db.commit()
        db.refresh(route)
        
        logger.info(f"Route saved: ID {route.id}")
        return route.id
    
    except Exception as error:
        db.rollback()
        logger.error(f"Error saving route: {error}")
        raise
    
    finally:
        db.close()


def save_telemetry(asset_id: str, lat: float, lon: float, 
                  speed: float, timestamp: str, event_type: str = None) -> int:
    """
    Save telemetry data to database
    
    Args:
        asset_id: Unique asset identifier
        lat, lon: GPS coordinates
        speed: Speed in km/h
        timestamp: ISO 8601 timestamp string
        event_type: Optional event type (MOVING, IDLE, SPEEDING)
    
    Returns:
        Telemetry log ID
    """
    db = SessionLocal()
    try:
        # Parse timestamp
        ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        telemetry = TelemetryLog(
            asset_id=asset_id,
            latitude=lat,
            longitude=lon,
            speed=speed,
            timestamp=ts,
            event_type=event_type
        )
        
        db.add(telemetry)
        db.commit()
        db.refresh(telemetry)
        
        return telemetry.id
    
    except Exception as error:
        db.rollback()
        logger.error(f"Error saving telemetry: {error}")
        raise
    
    finally:
        db.close()


def get_recent_routes(limit: int = 10) -> List[Dict]:
    """
    Get most recent routes from database
    
    Args:
        limit: Maximum number of routes to return
    
    Returns:
        List of route dictionaries
    """
    db = SessionLocal()
    try:
        routes = db.query(Route).order_by(Route.created_at.desc()).limit(limit).all()
        
        return [{
            "id": r.id,
            "start_lat": r.start_lat,
            "start_lon": r.start_lon,
            "end_lat": r.end_lat,
            "end_lon": r.end_lon,
            "distance_km": r.distance_km,
            "eta_min": r.eta_min,
            "created_at": r.created_at.isoformat()
        } for r in routes]
    
    finally:
        db.close()


def get_telemetry_for_training(limit: int = 1000) -> List[Dict]:
    """
    Get telemetry data for ML training
    
    Args:
        limit: Maximum number of records to return
    
    Returns:
        List of telemetry dictionaries
    """
    db = SessionLocal()
    try:
        logs = db.query(TelemetryLog).order_by(TelemetryLog.timestamp.desc()).limit(limit).all()
        
        return [{
            "asset_id": log.asset_id,
            "latitude": log.latitude,
            "longitude": log.longitude,
            "speed": log.speed,
            "timestamp": log.timestamp.isoformat(),
            "event_type": log.event_type
        } for log in logs]
    
    finally:
        db.close()
''')
    
    print("✅ ML and Database files created successfully!")
    print("   - retrain.py (RandomForest ML pipeline)")
    print("   - database.py (SQLAlchemy with PostgreSQL/SQLite)")

if __name__ == "__main__":
    create_files()
