"""
Database Initialization Script
Sets up database schema and loads initial data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import Database
from backend.geofence import GeofenceDetector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_database():
    """
    Initialize database schema
    """
    logger.info("Initializing database...")
    
    try:
        db = Database()
        logger.info("✓ Database initialized successfully")
        
        # Test the connection
        db.insert_telemetry(
            timestamp="2024-01-01 12:00:00",
            latitude=37.8719,
            longitude=-122.2585,
            speed=25.0
        )
        
        logger.info("✓ Database test successful")
        
        db.close()
        return True
    
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        return False


def load_campus_boundaries():
    """
    Load default campus boundaries
    """
    logger.info("Loading campus boundaries...")
    
    try:
        detector = GeofenceDetector()
        logger.info(f"✓ Loaded {len(detector.campuses)} campus boundaries")
        
        for campus in detector.campuses:
            logger.info(f"  - {campus['name']} ({campus['type']})")
        
        return True
    
    except Exception as e:
        logger.error(f"✗ Failed to load campus boundaries: {e}")
        return False


def download_osm_data():
    """
    Download OpenStreetMap data for routing
    """
    logger.info("Downloading OpenStreetMap data...")
    logger.info("This may take a few minutes...")
    
    try:
        from backend.routing import RoutingEngine
        
        engine = RoutingEngine()
        
        if engine.graph:
            logger.info(f"✓ OSM data loaded: {len(engine.graph.nodes)} nodes")
            return True
        else:
            logger.warning("✗ Failed to load OSM data")
            return False
    
    except Exception as e:
        logger.error(f"✗ OSM data download failed: {e}")
        return False


def verify_geocoding():
    """
    Verify geocoding service
    """
    logger.info("Verifying geocoding service...")
    
    try:
        from backend.geocoding import GeocodingService
        
        service = GeocodingService()
        
        # Test geocoding
        result = service.geocode("University of California, Berkeley")
        
        if result:
            logger.info(f"✓ Geocoding service operational")
            logger.info(f"  Test result: {result['formatted_address']}")
            return True
        else:
            logger.warning("✗ Geocoding test failed")
            return False
    
    except Exception as e:
        logger.error(f"✗ Geocoding verification failed: {e}")
        return False


def main():
    """
    Main initialization routine
    """
    logger.info("="*60)
    logger.info("Intelligent Geospatial Engine - Setup")
    logger.info("="*60)
    logger.info("")
    
    steps = [
        ("Database Initialization", initialize_database),
        ("Campus Boundaries", load_campus_boundaries),
        ("OpenStreetMap Data", download_osm_data),
        ("Geocoding Service", verify_geocoding),
    ]
    
    results = []
    
    for step_name, step_func in steps:
        logger.info(f"\n[Step] {step_name}")
        logger.info("-" * 60)
        
        success = step_func()
        results.append((step_name, success))
        
        logger.info("")
    
    # Summary
    logger.info("="*60)
    logger.info("Setup Summary")
    logger.info("="*60)
    
    for step_name, success in results:
        status = "✓ SUCCESS" if success else "✗ FAILED"
        logger.info(f"{status:12} - {step_name}")
    
    all_success = all(success for _, success in results)
    
    if all_success:
        logger.info("\n✓ All setup steps completed successfully!")
        logger.info("\nYou can now start the backend server:")
        logger.info("  cd backend")
        logger.info("  python main.py")
    else:
        logger.warning("\n⚠ Some setup steps failed. Check the errors above.")
    
    logger.info("")


if __name__ == "__main__":
    main()
