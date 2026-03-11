"""
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
