"""
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
    print("\n" + "="*50)
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
    
    print(f"\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Train Random Forest model
    print("\nTraining RandomForestRegressor...")
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
    
    print(f"
📊 Model Performance:")
    print(f"   Mean Absolute Error: {mae:.2f} minutes")
    print(f"   R² Score: {r2:.4f}")
    print(f"   Feature Importances:")
    for feature_name, importance in zip(X.columns, model.feature_importances_):
        print(f"      {feature_name}: {importance:.3f}")
    
    # Save model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"
✅ Model saved to {MODEL_PATH}")
    
    return {
        "mae": round(mae, 2),
        "r2_score": round(r2, 4),
        "samples_trained": len(X_train),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Run the retraining pipeline
    print("Starting retraining pipeline...\n")
    
    # Step 1: Download fresh OSM data (optional)
    # download_fresh_osm_data()
    
    # Step 2: Retrain the model
    metrics = retrain_model()
    
    print(f"\n{'='*50}")
    print("RETRAINING COMPLETE")
    print(f"{'='*50}")
    print(f"Timestamp: {metrics['timestamp']}")
    print(f"MAE: {metrics['mae']} min")
    print(f"R²: {metrics['r2_score']}")
