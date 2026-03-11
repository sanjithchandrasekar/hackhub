# 📐 Project Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
│                    (React + Leaflet.js)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Route   │  │ Geocode  │  │ Geofence │  │   Map    │        │
│  │  Panel   │  │  Panel   │  │  Panel   │  │   View   │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└────────────────────────────┬──────────────────────────────────┘
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Endpoints                          │  │
│  │  /route  /geofence  /geocode  /reverse-geocode           │  │
│  │  /telemetry  /campus-boundaries                          │  │
│  └────────┬─────────────┬─────────────┬─────────────────────┘  │
│           │             │             │                          │
│           ▼             ▼             ▼                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │  Routing    │ │  Geofence   │ │  Geocoding  │              │
│  │  Engine     │ │  Detector   │ │  Service    │              │
│  │             │ │             │ │             │              │
│  │ • OSMNX     │ │ • Shapely   │ │ • Nominatim │              │
│  │ • NetworkX  │ │ • Polygons  │ │ • Geopy     │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │           Telemetry Processor                           │  │
│  │  • GPS data collection                                  │  │
│  │  • Event detection                                      │  │
│  └──────────────────────────┬──────────────────────────────┘  │
└─────────────────────────────┼──────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Database Layer                              │
│  ┌──────────────────┐           ┌──────────────────┐           │
│  │   PostgreSQL     │    OR     │     SQLite       │           │
│  │   + PostGIS      │           │   (Fallback)     │           │
│  └──────────────────┘           └──────────────────┘           │
│                                                                  │
│  Tables:                                                         │
│  • telemetry        (GPS data, speeds, timestamps)              │
│  • geofence_events  (entry/exit events)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Machine Learning Pipeline                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Continuous Learning System                   │  │
│  │                                                           │  │
│  │  1. Fetch telemetry data                                 │  │
│  │  2. Extract features (distance, time, speed)             │  │
│  │  3. Train Random Forest model                            │  │
│  │  4. Update routing weights                               │  │
│  │  5. Save model to disk                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Stored Models:                                                  │
│  • eta_model.pkl  (ETA prediction)                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Data Sources                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ OpenStreetMap│  │  Nominatim   │  │ GPS Devices  │          │
│  │  (Road data) │  │  (Geocoding) │  │ (Telemetry)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### Frontend Layer (React)

**Technology Stack:**
- React 18.2
- Leaflet.js for mapping
- OpenStreetMap tiles

**Components:**
1. **MapView** - Main interactive map
   - Displays routes, markers, geofences
   - Handles map interactions
   - Renders polygons and polylines

2. **RoutePanel** - Route planning interface
   - Input start/end coordinates
   - Trigger route calculations
   - Display distance and ETA

3. **GeocodePanel** - Address search
   - Forward geocoding (address → coords)
   - Reverse geocoding (coords → address)
   - Tabbed interface

4. **GeofencePanel** - Boundary checking
   - Check if point is inside geofence
   - Display campus information
   - Show distance to boundary

### Backend Layer (Python)

**Technology Stack:**
- FastAPI (async web framework)
- Uvicorn (ASGI server)
- Pydantic (data validation)

**Core Modules:**

1. **routing.py** - Intelligent Routing
   ```
   OpenStreetMap → OSMNX → NetworkX Graph → Dijkstra → Route
   ```
   - Downloads road network data
   - Builds weighted directed graph
   - Calculates shortest paths
   - Estimates travel time

2. **geofence.py** - Spatial Analysis
   ```
   Point + Polygon → Shapely → Contains Check → Result
   ```
   - Loads campus boundaries
   - Point-in-polygon detection
   - Distance calculations
   - Entry/exit event detection

3. **geocoding.py** - Address Resolution
   ```
   Address/Coords → Nominatim API → Normalized Data
   ```
   - Forward geocoding
   - Reverse geocoding
   - Rate limiting
   - Error handling

4. **telemetry.py** - Data Processing
   ```
   GPS Data → Validation → Storage → Event Detection
   ```
   - Receives GPS telemetry
   - Stores in database
   - Detects geofence events
   - Calculates statistics

5. **retrain.py** - Machine Learning
   ```
   Telemetry → Features → Random Forest → Updated Model
   ```
   - Fetches training data
   - Extracts features
   - Trains ML models
   - Updates routing weights

6. **database.py** - Data Persistence
   ```
   Application → ORM/SQL → PostgreSQL/SQLite
   ```
   - Database abstraction
   - PostgreSQL with PostGIS
   - SQLite fallback
   - Schema management

### Data Flow

#### Route Calculation Flow
```
User Input (coords)
    ↓
Frontend (RoutePanel)
    ↓
API POST /route
    ↓
RoutingEngine.calculate_route()
    ↓
NetworkX shortest_path()
    ↓
Route Coordinates + Metrics
    ↓
Frontend (MapView)
    ↓
Leaflet Polyline on Map
```

#### Geofence Detection Flow
```
GPS Coordinates
    ↓
API POST /geofence
    ↓
GeofenceDetector.check_point()
    ↓
Shapely Point-in-Polygon
    ↓
Inside/Outside + Campus Name
    ↓
UI Display + Marker
```

#### Telemetry Learning Flow
```
GPS Telemetry
    ↓
API POST /telemetry
    ↓
Database Storage
    ↓
(Periodic) Retraining Script
    ↓
Feature Extraction
    ↓
Model Training
    ↓
Updated Predictions
```

## Technology Choices & Rationale

### Why FastAPI?
- ✅ Automatic API documentation (OpenAPI)
- ✅ Async/await support for better performance
- ✅ Built-in Pydantic validation
- ✅ Modern Python type hints
- ✅ Easy to learn and teach

### Why OSMNX?
- ✅ Direct OpenStreetMap integration
- ✅ Built on NetworkX for graph algorithms
- ✅ Handles spatial data automatically
- ✅ Free and open data source
- ✅ Active development

### Why Shapely?
- ✅ Industry-standard geometry library
- ✅ Fast C++ backend (GEOS)
- ✅ Simple, Pythonic API
- ✅ Widely used in GIS applications

### Why React + Leaflet?
- ✅ React is widely taught and known
- ✅ Leaflet is lighter than Google Maps
- ✅ OpenStreetMap is free
- ✅ Easy to customize
- ✅ Mobile-friendly

### Why PostgreSQL/PostGIS?
- ✅ PostGIS adds spatial capabilities
- ✅ Industry standard for geospatial data
- ✅ Powerful indexing for location queries
- ✅ Optional (SQLite fallback provided)

## Scalability Considerations

### Current Architecture (Demo/Hackathon)
- Single server deployment
- In-memory caching
- Synchronized processing
- SQLite database

### Production Scale-Up Path

1. **Database Layer:**
   ```
   SQLite → PostgreSQL → PostgreSQL + Read Replicas
   ```

2. **API Layer:**
   ```
   Single Instance → Load Balancer → Multiple Instances
   ```

3. **Caching Layer:**
   ```
   In-Memory → Redis → Redis Cluster
   ```

4. **Storage:**
   ```
   Local Files → S3/Object Storage
   ```

5. **Machine Learning:**
   ```
   Single Model → Model Versioning → A/B Testing
   ```

## Performance Optimizations

### Implemented
- ✅ Graph caching (OSM data)
- ✅ Async endpoints
- ✅ Database indexing
- ✅ Rate limiting (Nominatim)

### Future Enhancements
- ⬜ Redis caching for routes
- ⬜ CDN for frontend assets
- ⬜ Database connection pooling
- ⬜ Horizontal scaling
- ⬜ Model serving infrastructure

## Security Considerations

### Current (Development)
- No authentication
- Open CORS policy
- No rate limiting (except Nominatim)

### Production Recommendations
1. Add API authentication (JWT tokens)
2. Implement rate limiting
3. Restrict CORS to specific domains
4. Use HTTPS only
5. Validate all inputs
6. Add API key management
7. Monitor for abuse

## Monitoring & Observability

### Logging
- Structured logging with Python logging module
- Log levels: INFO, WARNING, ERROR
- Separate logs for each module

### Metrics (Future)
- API response times
- Route calculation performance
- Database query performance
- ML model accuracy
- Active users

### Health Checks
- `/` endpoint for basic health
- Database connectivity check
- External API status

## Deployment Options

### Local Development
```
Backend: python main.py
Frontend: npm start
```

### Docker (Future)
```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
  postgres:
    image: postgis/postgis
```

### Cloud (Future)
- Backend: AWS Lambda / Google Cloud Run
- Frontend: Netlify / Vercel
- Database: AWS RDS / Google Cloud SQL
- Storage: S3 / GCS

## Testing Strategy

### Unit Tests
- Test individual modules
- Mock external dependencies
- Coverage target: 70%+

### Integration Tests
- Test API endpoints
- Test database operations
- Test ML pipeline

### E2E Tests
- Selenium/Playwright for UI
- Test complete user flows
- Automated regression testing

---

**This architecture is designed to be:**
- 📚 **Educational** - Easy to understand and learn from
- 🚀 **Scalable** - Clear path from demo to production
- 🔧 **Maintainable** - Modular and well-documented
- 🎯 **Practical** - Solves real geospatial problems
