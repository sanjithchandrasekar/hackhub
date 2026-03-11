# 📡 API Documentation

## Base URL
```
http://localhost:8000
```

## Interactive Documentation
FastAPI provides automatic interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Endpoints

### 1. Health Check

**GET** `/`

Check if the API is running.

**Response**
```json
{
  "status": "online",
  "service": "Intelligent Geospatial Engine",
  "version": "1.0.0"
}
```

**Example**
```bash
curl http://localhost:8000/
```

---

### 2. Calculate Route

**POST** `/route`

Calculate the optimal route between two geographic points using OpenStreetMap data.

**Request Body**
```json
{
  "start_lat": 37.8719,
  "start_lon": -122.2585,
  "end_lat": 37.8690,
  "end_lon": -122.2560
}
```

**Response**
```json
{
  "route": [
    [37.8719, -122.2585],
    [37.8710, -122.2590],
    [37.8690, -122.2560]
  ],
  "distance": 2.34,
  "estimated_time": 4.5,
  "status": "success"
}
```

**Fields**
- `route`: Array of [latitude, longitude] coordinates
- `distance`: Distance in kilometers
- `estimated_time`: Estimated time in minutes
- `status`: "success" or error message

**Example**
```bash
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{
    "start_lat": 37.8719,
    "start_lon": -122.2585,
    "end_lat": 37.8690,
    "end_lon": -122.2560
  }'
```

**Errors**
- 500: Route calculation failed
- 400: Invalid coordinates

---

### 3. Check Geofence

**POST** `/geofence`

Check if a point is inside a defined geofence boundary.

**Request Body**
```json
{
  "latitude": 37.8719,
  "longitude": -122.2585
}
```

**Response (Inside)**
```json
{
  "inside_geofence": true,
  "campus_name": "UC Berkeley Campus",
  "distance_to_edge": 0.542
}
```

**Response (Outside)**
```json
{
  "inside_geofence": false,
  "campus_name": null,
  "distance_to_edge": 2.134
}
```

**Fields**
- `inside_geofence`: Boolean indicating if point is inside
- `campus_name`: Name of campus if inside, null otherwise
- `distance_to_edge`: Distance to nearest edge in kilometers

**Example**
```bash
curl -X POST http://localhost:8000/geofence \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 37.8719,
    "longitude": -122.2585
  }'
```

---

### 4. Geocode Address

**POST** `/geocode`

Convert an address to geographic coordinates.

**Request Body**
```json
{
  "address": "1600 Amphitheatre Parkway, Mountain View, CA"
}
```

**Response**
```json
{
  "latitude": 37.4220936,
  "longitude": -122.0852802,
  "formatted_address": "1600 Amphitheatre Parkway, Mountain View, CA 94043, United States"
}
```

**Fields**
- `latitude`: Latitude coordinate
- `longitude`: Longitude coordinate
- `formatted_address`: Standardized address string

**Example**
```bash
curl -X POST http://localhost:8000/geocode \
  -H "Content-Type: application/json" \
  -d '{
    "address": "University of California, Berkeley"
  }'
```

**Errors**
- 404: Address not found
- 500: Geocoding service error

**Rate Limits**
- Nominatim: 1 request per second
- Built-in rate limiting included

---

### 5. Reverse Geocode

**POST** `/reverse-geocode`

Convert geographic coordinates to an address.

**Request Body**
```json
{
  "latitude": 37.8719,
  "longitude": -122.2585
}
```

**Response**
```json
{
  "address": "Sather Tower, Campanile Way, Berkeley, CA 94720, United States",
  "city": "Berkeley",
  "country": "United States",
  "postal_code": "94720"
}
```

**Fields**
- `address`: Full formatted address
- `city`: City name (may be null)
- `country`: Country name (may be null)
- `postal_code`: Postal/ZIP code (may be null)

**Example**
```bash
curl -X POST http://localhost:8000/reverse-geocode \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 37.8719,
    "longitude": -122.2585
  }'
```

**Errors**
- 404: Location not found
- 500: Reverse geocoding service error

---

### 6. Submit Telemetry

**POST** `/telemetry`

Submit GPS telemetry data for collection and learning.

**Request Body**
```json
{
  "timestamp": "2024-01-01T12:00:00",
  "latitude": 37.8719,
  "longitude": -122.2585,
  "speed": 25.5
}
```

**Response**
```json
{
  "status": "success",
  "message": "Telemetry data recorded"
}
```

**Fields**
- `timestamp`: ISO 8601 format timestamp
- `latitude`: GPS latitude
- `longitude`: GPS longitude
- `speed`: Speed in km/h

**Example**
```bash
curl -X POST http://localhost:8000/telemetry \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-01-01T12:00:00",
    "latitude": 37.8719,
    "longitude": -122.2585,
    "speed": 25.5
  }'
```

**Notes**
- Stores data in database
- Triggers geofence event detection
- Used for model retraining

---

### 7. Get Campus Boundaries

**GET** `/campus-boundaries`

Retrieve all defined campus geofence boundaries.

**Response**
```json
{
  "boundaries": [
    {
      "name": "UC Berkeley Campus",
      "polygon": [
        [-122.2675, 37.8650],
        [-122.2675, 37.8775],
        [-122.2505, 37.8775],
        [-122.2505, 37.8650],
        [-122.2675, 37.8650]
      ],
      "type": "university"
    }
  ]
}
```

**Fields**
- `boundaries`: Array of campus boundary objects
- `name`: Campus name
- `polygon`: Array of [longitude, latitude] coordinates
- `type`: Campus type (e.g., "university")

**Example**
```bash
curl http://localhost:8000/campus-boundaries
```

**Usage**
- Used by frontend to display geofence boundaries on map
- Polygon coordinates in [lon, lat] format (GeoJSON standard)

---

## Data Models

### RouteRequest
```typescript
{
  start_lat: number;    // -90 to 90
  start_lon: number;    // -180 to 180
  end_lat: number;      // -90 to 90
  end_lon: number;      // -180 to 180
}
```

### GeofenceRequest
```typescript
{
  latitude: number;     // -90 to 90
  longitude: number;    // -180 to 180
}
```

### GeocodeRequest
```typescript
{
  address: string;      // Any valid address string
}
```

### TelemetryData
```typescript
{
  timestamp: string;    // ISO 8601 format
  latitude: number;     // -90 to 90
  longitude: number;    // -180 to 180
  speed: number;        // km/h, >= 0
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message description"
}
```

### Common HTTP Status Codes
- `200`: Success
- `400`: Bad Request (invalid input)
- `404`: Not Found (resource not found)
- `500`: Internal Server Error

---

## CORS Configuration

The API allows requests from any origin for development:

```python
allow_origins=["*"]
```

For production, restrict to specific domains:

```python
allow_origins=[
  "https://yourdomain.com",
  "https://www.yourdomain.com"
]
```

---

## Rate Limiting

### Nominatim API
- Geocoding and reverse geocoding use Nominatim
- Rate limit: 1 request per second
- Built-in rate limiting in `geocoding.py`
- Consider caching for production use

### API Endpoints
- No rate limiting implemented by default
- Add rate limiting for production:
  - Use FastAPI middleware
  - Redis-based rate limiting
  - Token bucket algorithm

---

## Authentication

Currently, the API has no authentication for development/demo purposes.

For production, add authentication:

1. **API Keys**
```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")
```

2. **OAuth2**
```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

---

## Versioning

Current version: `1.0.0`

Future versions can be prefixed:
```
/v1/route
/v2/route
```

---

## Testing

### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/route",
    json={
        "start_lat": 37.8719,
        "start_lon": -122.2585,
        "end_lat": 37.8690,
        "end_lon": -122.2560
    }
)

print(response.json())
```

### JavaScript
```javascript
fetch('http://localhost:8000/route', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    start_lat: 37.8719,
    start_lon: -122.2585,
    end_lat: 37.8690,
    end_lon: -122.2560
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## WebSocket Support (Future Enhancement)

For real-time telemetry streaming:

```python
@app.websocket("/ws/telemetry")
async def telemetry_websocket(websocket: WebSocket):
    await websocket.accept()
    # Stream telemetry data
```

---

## Performance Considerations

1. **Caching**: Add Redis for frequently accessed routes
2. **Database Indexing**: Already indexed on timestamp fields
3. **Async Operations**: All endpoints use async/await
4. **Connection Pooling**: Consider for database connections

---

## Support

- Interactive docs: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`
- Source code: `backend/main.py`
