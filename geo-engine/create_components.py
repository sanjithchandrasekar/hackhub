"""
Create Frontend React Components for GeoEngine - Bengaluru
"""

import os

def create_frontend_components():
    """Create all React component files"""
    
    # Ensure directories exist
    os.makedirs("frontend/src/components", exist_ok=True)
    
    # Component 1: MapView.jsx
    with open("frontend/src/components/MapView.jsx", "w", encoding="utf-8") as f:
        f.write('''/**
 * MapView Component
 * Interactive Leaflet map centered on Bengaluru, India
 * 
 * Displays:
 * - Base OpenStreetMap tiles
 * - Route polylines in blue
 * - Campus boundary polygons in green
 * - GPS markers in red
 * - Live GPS simulation
 */

import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Polyline, Polygon, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import axios from 'axios';

// Fix for default marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Bengaluru center coordinates
const BENGALURU_CENTER = [12.9716, 77.5946];
const DEFAULT_ZOOM = 12;

function MapView({ routeCoords, gpsPoints }) {
  const [campusPolygons, setCampusPolygons] = useState([]);
  const [liveGPS, setLiveGPS] = useState(null);

  // Fetch campus boundaries on mount
  useEffect(() => {
    // Define Bengaluru campus polygons
    const campuses = [
      {
        name: "IISc Campus",
        coords: [
          [13.0225, 77.5640],
          [13.0225, 77.5720],
          [13.0150, 77.5720],
          [13.0150, 77.5640],
          [13.0225, 77.5640]
        ]
      },
      {
        name: "Electronic City",
        coords: [
          [12.8400, 77.6600],
          [12.8400, 77.6700],
          [12.8300, 77.6700],
          [12.8300, 77.6600],
          [12.8400, 77.6600]
        ]
      },
      {
        name: "Whitefield Tech Park",
        coords: [
          [12.9850, 77.7450],
          [12.9850, 77.7550],
          [12.9750, 77.7550],
          [12.9750, 77.7450],
          [12.9850, 77.7450]
        ]
      }
    ];
    
    setCampusPolygons(campuses);
  }, []);

  // Simulate live GPS movement every 2 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      // Generate random GPS point near Bengaluru
      const randomLat = 12.9716 + (Math.random() - 0.5) * 0.1;
      const randomLon = 77.5946 + (Math.random() - 0.5) * 0.1;
      
      setLiveGPS({
        lat: randomLat,
        lon: randomLon,
        timestamp: new Date().toISOString()
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ height: '100%', width: '100%' }}>
      <MapContainer
        center={BENGALURU_CENTER}
        zoom={DEFAULT_ZOOM}
        style={{ height: '100%', width: '100%' }}
      >
        {/* OpenStreetMap base layer */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Route polyline */}
        {routeCoords && routeCoords.length > 0 && (
          <Polyline
            positions={routeCoords}
            pathOptions={{ color: '#2196F3', weight: 4 }}
          >
            <Popup>Route: {routeCoords.length} waypoints</Popup>
          </Polyline>
        )}

        {/* Campus boundary polygons */}
        {campusPolygons.map((campus, idx) => (
          <Polygon
            key={idx}
            positions={campus.coords}
            pathOptions={{
              color: '#4CAF50',
              weight: 2,
              fillColor: '#4CAF50',
              fillOpacity: 0.1,
              dashArray: '5, 10'
            }}
          >
            <Popup>{campus.name}</Popup>
          </Polygon>
        ))}

        {/* GPS markers from props */}
        {gpsPoints && gpsPoints.map((point, idx) => (
          <Marker key={idx} position={[point.lat, point.lon]}>
            <Popup>
              GPS Point<br />
              Lat: {point.lat.toFixed(4)}<br />
              Lon: {point.lon.toFixed(4)}
            </Popup>
          </Marker>
        ))}

        {/* Live GPS simulation marker */}
        {liveGPS && (
          <Marker
            position={[liveGPS.lat, liveGPS.lon]}
            icon={new L.Icon({
              iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
              shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
              iconSize: [25, 41],
              iconAnchor: [12, 41],
              popupAnchor: [1, -34],
              shadowSize: [41, 41]
            })}
          >
            <Popup>
              Live GPS<br />
              {new Date(liveGPS.timestamp).toLocaleTimeString()}
            </Popup>
          </Marker>
        )}
      </MapContainer>
    </div>
  );
}

export default MapView;
''')

    # Component 2: RoutePanel.jsx
    with open("frontend/src/components/RoutePanel.jsx", "w", encoding="utf-8") as f:
        f.write('''/**
 * RoutePanel Component
 * UI for route planning between two GPS coordinates
 * 
 * Features:
 * - Input fields for start/end coordinates
 * - Default Bengaluru coordinates
 * - Loading spinner during API call
 * - Result display with distance and ETA
 */

import React, { useState } from 'react';
import axios from 'axios';

function RoutePanel({ onRouteCalculated }) {
  // Default coordinates in Bengaluru
  const [startLat, setStartLat] = useState('12.9716');
  const [startLon, setStartLon] = useState('77.5946');
  const [endLat, setEndLat] = useState('12.9350');
  const [endLon, setEndLon] = useState('77.6244');
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleCalculateRoute = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/route', {
        start_lat: parseFloat(startLat),
        start_lon: parseFloat(startLon),
        end_lat: parseFloat(endLat),
        end_lon: parseFloat(endLon)
      });
      
      setResult(response.data);
      
      // Pass route coordinates to parent
      if (onRouteCalculated && response.data.route) {
        onRouteCalculated(response.data.route);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Route calculation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.card}>
      <h3 style={styles.title}>🗺️ Route Planner</h3>
      
      <div style={styles.form}>
        <div style={styles.inputGroup}>
          <label style={styles.label}>Start Latitude</label>
          <input
            type="number"
            step="0.0001"
            value={startLat}
            onChange={(e) => setStartLat(e.target.value)}
            style={styles.input}
          />
        </div>
        
        <div style={styles.inputGroup}>
          <label style={styles.label}>Start Longitude</label>
          <input
            type="number"
            step="0.0001"
            value={startLon}
            onChange={(e) => setStartLon(e.target.value)}
            style={styles.input}
          />
        </div>
        
        <div style={styles.inputGroup}>
          <label style={styles.label}>End Latitude</label>
          <input
            type="number"
            step="0.0001"
            value={endLat}
            onChange={(e) => setEndLat(e.target.value)}
            style={styles.input}
          />
        </div>
        
        <div style={styles.inputGroup}>
          <label style={styles.label}>End Longitude</label>
          <input
            type="number"
            step="0.0001"
            value={endLon}
            onChange={(e) => setEndLon(e.target.value)}
            style={styles.input}
          />
        </div>
        
        <button
          onClick={handleCalculateRoute}
          disabled={loading}
          style={{...styles.button, opacity: loading ? 0.6 : 1}}
        >
          {loading ? 'Calculating...' : 'Calculate Route'}
        </button>
      </div>
      
      {error && (
        <div style={styles.error}>{error}</div>
      )}
      
      {result && (
        <div style={styles.result}>
          <h4 style={styles.resultTitle}>✅ Route Found</h4>
          <p><strong>Distance:</strong> {result.distance_km} km</p>
          <p><strong>ETA:</strong> {result.estimated_time_min} minutes</p>
          <p><strong>Waypoints:</strong> {result.waypoints_count || result.route?.length}</p>
        </div>
      )}
    </div>
  );
}

const styles = {
  card: {
    background: 'white',
    borderRadius: '8px',
    padding: '20px',
    marginBottom: '20px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  title: {
    color: '#2196F3',
    marginTop: 0,
    marginBottom: '15px'
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px'
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column'
  },
  label: {
    fontSize: '13px',
    fontWeight: '600',
    marginBottom: '4px',
    color: '#555'
  },
  input: {
    padding: '8px 12px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px'
  },
  button: {
    background: '#2196F3',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    padding: '12px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
    marginTop: '8px'
  },
  result: {
    marginTop: '15px',
    padding: '12px',
    background: '#E3F2FD',
    borderRadius: '4px',
    borderLeft: '4px solid #2196F3'
  },
  resultTitle: {
    margin: '0 0 8px 0',
    color: '#1976D2'
  },
  error: {
    marginTop: '15px',
    padding: '12px',
    background: '#FFEBEE',
    borderRadius: '4px',
    color: '#C62828',
    borderLeft: '4px solid #C62828'
  }
};

export default RoutePanel;
''')

    # Component 3: GeofencePanel.jsx
    with open("frontend/src/components/GeofencePanel.jsx", "w", encoding="utf-8") as f:
        f.write('''/**
 * GeofencePanel Component
 * UI for checking if coordinates are inside campus boundaries
 * 
 * Features:
 * - Input fields for latitude/longitude
 * - "Use Current Location" button
 * - Inside/outside status with color coding
 * - Campus name display
 * - Distance to nearest boundary
 */

import React, { useState } from 'react';
import axios from 'axios';

function GeofencePanel({ onLocationChecked }) {
  const [lat, setLat] = useState('13.0200');
  const [lon, setLon] = useState('77.5680');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleCheckGeofence = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/geofence', {
        lat: parseFloat(lat),
        lon: parseFloat(lon)
      });
      
      setResult(response.data);
      
      // Pass location to parent
      if (onLocationChecked) {
        onLocationChecked({ lat: parseFloat(lat), lon: parseFloat(lon) });
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Geofence check failed');
    } finally {
      setLoading(false);
    }
  };

  const handleUseCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLat(position.coords.latitude.toFixed(4));
          setLon(position.coords.longitude.toFixed(4));
        },
        (error) => {
          setError('Could not get current location: ' + error.message);
        }
      );
    } else {
      setError('Geolocation is not supported by this browser');
    }
  };

  return (
    <div style={styles.card}>
      <h3 style={styles.title}>🏢 Geofence Checker</h3>
      
      <div style={styles.form}>
        <div style={styles.inputGroup}>
          <label style={styles.label}>Latitude</label>
          <input
            type="number"
            step="0.0001"
            value={lat}
            onChange={(e) => setLat(e.target.value)}
            style={styles.input}
          />
        </div>
        
        <div style={styles.inputGroup}>
          <label style={styles.label}>Longitude</label>
          <input
            type="number"
            step="0.0001"
            value={lon}
            onChange={(e) => setLon(e.target.value)}
            style={styles.input}
          />
        </div>
        
        <button
          onClick={handleUseCurrentLocation}
          style={styles.buttonSecondary}
        >
          📍 Use Current Location
        </button>
        
        <button
          onClick={handleCheckGeofence}
          disabled={loading}
          style={{...styles.button, opacity: loading ? 0.6 : 1}}
        >
          {loading ? 'Checking...' : 'Check Geofence'}
        </button>
      </div>
      
      {error && (
        <div style={styles.error}>{error}</div>
      )}
      
      {result && (
        <div style={result.inside_geofence ? styles.resultInside : styles.resultOutside}>
          <h4 style={styles.resultTitle}>
            {result.inside_geofence ? '✅ Inside Geofence' : '❌ Outside Geofence'}
          </h4>
          {result.campus_name && (
            <p><strong>Campus:</strong> {result.campus_name}</p>
          )}
          <p><strong>Distance to Nearest:</strong> {result.distance_to_nearest?.toFixed(2)} m</p>
          {result.event_type && (
            <div style={styles.badge}>
              {result.event_type}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const styles = {
  card: {
    background: 'white',
    borderRadius: '8px',
    padding: '20px',
    marginBottom: '20px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  title: {
    color: '#2196F3',
    marginTop: 0,
    marginBottom: '15px'
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px'
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column'
  },
  label: {
    fontSize: '13px',
    fontWeight: '600',
    marginBottom: '4px',
    color: '#555'
  },
  input: {
    padding: '8px 12px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px'
  },
  button: {
    background: '#2196F3',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    padding: '12px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer'
  },
  buttonSecondary: {
    background: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    padding: '10px',
    fontSize: '13px',
    fontWeight: '600',
    cursor: 'pointer'
  },
  resultInside: {
    marginTop: '15px',
    padding: '12px',
    background: '#E8F5E9',
    borderRadius: '4px',
    borderLeft: '4px solid #4CAF50'
  },
  resultOutside: {
    marginTop: '15px',
    padding: '12px',
    background: '#FFEBEE',
    borderRadius: '4px',
    borderLeft: '4px solid #F44336'
  },
  resultTitle: {
    margin: '0 0 8px 0',
    color: '#333'
  },
  badge: {
    display: 'inline-block',
    marginTop: '8px',
    padding: '4px 12px',
    background: '#FF9800',
    color: 'white',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: '600'
  },
  error: {
    marginTop: '15px',
    padding: '12px',
    background: '#FFEBEE',
    borderRadius: '4px',
    color: '#C62828',
    borderLeft: '4px solid #C62828'
  }
};

export default GeofencePanel;
''')

    # Component 4: GeocodePanel.jsx
    with open("frontend/src/components/GeocodePanel.jsx", "w", encoding="utf-8") as f:
        f.write('''/**
 * GeocodePanel Component
 * UI for geocoding and reverse geocoding
 * 
 * Features:
 * - Two tabs: Forward and Reverse geocoding
 * - Address to coordinates conversion
 * - Coordinates to address conversion
 * - Structured address display
 */

import React, { useState } from 'react';
import axios from 'axios';

function GeocodePanel() {
  const [activeTab, setActiveTab] = useState('forward');
  
  // Forward geocoding state
  const [address, setAddress] = useState('MG Road, Bengaluru, Karnataka');
  const [forwardLoading, setForwardLoading] = useState(false);
  const [forwardResult, setForwardResult] = useState(null);
  const [forwardError, setForwardError] = useState(null);
  
  // Reverse geocoding state
  const [revLat, setRevLat] = useState('12.9716');
  const [revLon, setRevLon] = useState('77.5946');
  const [reverseLoading, setReverseLoading] = useState(false);
  const [reverseResult, setReverseResult] = useState(null);
  const [reverseError, setReverseError] = useState(null);

  const handleForwardGeocode = async () => {
    setForwardLoading(true);
    setForwardError(null);
    
    try {
      const response = await axios.post('/geocode', {
        address: address
      });
      
      setForwardResult(response.data);
    } catch (err) {
      setForwardError(err.response?.data?.detail || 'Geocoding failed');
    } finally {
      setForwardLoading(false);
    }
  };

  const handleReverseGeocode = async () => {
    setReverseLoading(true);
    setReverseError(null);
    
    try {
      const response = await axios.post('/reverse-geocode', {
        lat: parseFloat(revLat),
        lon: parseFloat(revLon)
      });
      
      setReverseResult(response.data);
    } catch (err) {
      setReverseError(err.response?.data?.detail || 'Reverse geocoding failed');
    } finally {
      setReverseLoading(false);
    }
  };

  return (
    <div style={styles.card}>
      <h3 style={styles.title}>📍 Geocoding</h3>
      
      {/* Tabs */}
      <div style={styles.tabs}>
        <button
          onClick={() => setActiveTab('forward')}
          style={{
            ...styles.tab,
            ...(activeTab === 'forward' ? styles.tabActive : {})
          }}
        >
          Address → Coords
        </button>
        <button
          onClick={() => setActiveTab('reverse')}
          style={{
            ...styles.tab,
            ...(activeTab === 'reverse' ? styles.tabActive : {})
          }}
        >
          Coords → Address
        </button>
      </div>
      
      {/* Forward Geocoding Tab */}
      {activeTab === 'forward' && (
        <div style={styles.tabContent}>
          <div style={styles.inputGroup}>
            <label style={styles.label}>Address</label>
            <input
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              style={styles.input}
              placeholder="e.g., Koramangala, Bengaluru"
            />
          </div>
          
          <button
            onClick={handleForwardGeocode}
            disabled={forwardLoading}
            style={{...styles.button, opacity: forwardLoading ? 0.6 : 1}}
          >
            {forwardLoading ? 'Geocoding...' : 'Find Coordinates'}
          </button>
          
          {forwardError && (
            <div style={styles.error}>{forwardError}</div>
          )}
          
          {forwardResult && (
            <div style={styles.result}>
              <h4 style={styles.resultTitle}>📍 Location Found</h4>
              <p><strong>Latitude:</strong> {forwardResult.lat}</p>
              <p><strong>Longitude:</strong> {forwardResult.lon}</p>
              <p><strong>Address:</strong> {forwardResult.display_name}</p>
              {forwardResult.city && <p><strong>City:</strong> {forwardResult.city}</p>}
            </div>
          )}
        </div>
      )}
      
      {/* Reverse Geocoding Tab */}
      {activeTab === 'reverse' && (
        <div style={styles.tabContent}>
          <div style={styles.inputGroup}>
            <label style={styles.label}>Latitude</label>
            <input
              type="number"
              step="0.0001"
              value={revLat}
              onChange={(e) => setRevLat(e.target.value)}
              style={styles.input}
            />
          </div>
          
          <div style={styles.inputGroup}>
            <label style={styles.label}>Longitude</label>
            <input
              type="number"
              step="0.0001"
              value={revLon}
              onChange={(e) => setRevLon(e.target.value)}
              style={styles.input}
            />
          </div>
          
          <button
            onClick={handleReverseGeocode}
            disabled={reverseLoading}
            style={{...styles.button, opacity: reverseLoading ? 0.6 : 1}}
          >
            {reverseLoading ? 'Finding Address...' : 'Find Address'}
          </button>
          
          {reverseError && (
            <div style={styles.error}>{reverseError}</div>
          )}
          
          {reverseResult && (
            <div style={styles.result}>
              <h4 style={styles.resultTitle}>📍 Address Found</h4>
              <p><strong>Address:</strong> {reverseResult.display_name}</p>
              {reverseResult.road && <p><strong>Road:</strong> {reverseResult.road}</p>}
              {reverseResult.city && <p><strong>City:</strong> {reverseResult.city}</p>}
              {reverseResult.postcode && <p><strong>Postcode:</strong> {reverseResult.postcode}</p>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const styles = {
  card: {
    background: 'white',
    borderRadius: '8px',
    padding: '20px',
    marginBottom: '20px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  title: {
    color: '#2196F3',
    marginTop: 0,
    marginBottom: '15px'
  },
  tabs: {
    display: 'flex',
    gap: '8px',
    marginBottom: '15px',
    borderBottom: '2px solid #f0f0f0'
  },
  tab: {
    flex: 1,
    padding: '10px',
    background: 'transparent',
    border: 'none',
    borderBottom: '2px solid transparent',
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: '600',
    color: '#666',
    marginBottom: '-2px'
  },
  tabActive: {
    color: '#2196F3',
    borderBottom: '2px solid #2196F3'
  },
  tabContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px'
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column'
  },
  label: {
    fontSize: '13px',
    fontWeight: '600',
    marginBottom: '4px',
    color: '#555'
  },
  input: {
    padding: '8px 12px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px'
  },
  button: {
    background: '#2196F3',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    padding: '12px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer'
  },
  result: {
    marginTop: '15px',
    padding: '12px',
    background: '#E3F2FD',
    borderRadius: '4px',
    borderLeft: '4px solid #2196F3'
  },
  resultTitle: {
    margin: '0 0 8px 0',
    color: '#1976D2'
  },
  error: {
    marginTop: '15px',
    padding: '12px',
    background: '#FFEBEE',
    borderRadius: '4px',
    color: '#C62828',
    borderLeft: '4px solid #C62828'
  }
};

export default GeocodePanel;
''')

    print("✅ All frontend components created successfully!")
    print("   - MapView.jsx (Leaflet map centered on Bengaluru)")
    print("   - RoutePanel.jsx (Route planner UI)")
    print("   - GeofencePanel.jsx (Geofence checker UI)")
    print("   - GeocodePanel.jsx (Geocoding UI with tabs)")

if __name__ == "__main__":
    create_frontend_components()
