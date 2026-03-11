"""
Update existing components with enhanced styling and features
- RoutePanel.jsx
- GeofencePanel.jsx
- GeocodePanel.jsx
"""

import os

#Enhanced RoutePanel
route_panel = '''import React, { useState } from 'react';
import axios from 'axios';

function RoutePanel({ onRouteCalculated, darkMode }) {
  const [startLat, setStartLat] = useState('12.9716');
  const [startLon, setStartLon] = useState('77.5946');
  const [endLat, setEndLat] = useState('12.9350');
  const [endLon, setEndLon] = useState('77.6244');
  const [mode, setMode] = useState('fastest');
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [alternatives, setAlternatives] = useState([]);

  const handleCalculateRoute = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/route', {
        start_lat: parseFloat(startLat),
        start_lon: parseFloat(startLon),
        end_lat: parseFloat(endLat),
        end_lon: parseFloat(endLon),
        mode: mode
      });
      
      setResult(response.data);
      
      if (onRouteCalculated && response.data.route) {
        onRouteCalculated(response.data.route);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Route calculation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleGetAlternatives = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/route/alternatives', {
        start_lat: parseFloat(startLat),
        start_lon: parseFloat(startLon),
        end_lat: parseFloat(endLat),
        end_lon: parseFloat(endLon)
      });
      
      setAlternatives(response.data.routes || []);
    } catch (err) {
      setError('Failed to get alternative routes');
    } finally {
      setLoading(false);
    }
  };

  const quickLocations = [
    { name: 'City Center', lat: 12.9716, lon: 77.5946 },
    { name: 'IISc Campus', lat: 13.0200, lon: 77.5680 },
    { name: 'Electronic City', lat: 12.8400, lon: 77.6650 },
    { name: 'Whitefield', lat: 12.9800, lon: 77.7500 },
  ];

  const setQuickLocation = (location, isStart) => {
    if (isStart) {
      setStartLat(location.lat.toString());
      setStartLon(location.lon.toString());
    } else {
      setEndLat(location.lat.toString());
      setEndLon(location.lon.toString());
    }
  };

  return (
    <div className="card">
      <h3 className="card-title">🗺️ Route Planner</h3>
      
      <div className="form-group">
        <label className="form-label">Route Mode</label>
        <select 
          className="form-input"
          value={mode}
          onChange={(e) => setMode(e.target.value)}
        >
          <option value="fastest">⚡ Fastest Route</option>
          <option value="shortest">📏 Shortest Route</option>
          <option value="balanced">⚖️ Balanced Route</option>
        </select>
      </div>

      <div className="form-group">
        <label className="form-label">Start Location</label>
        <div className="flex gap-1">
          <input
            type="number"
            step="0.0001"
            value={startLat}
            onChange={(e) => setStartLat(e.target.value)}
            className="form-input"
            placeholder="Latitude"
          />
          <input
            type="number"
            step="0.0001"
            value={startLon}
            onChange={(e) => setStartLon(e.target.value)}
            className="form-input"
            placeholder="Longitude"
          />
        </div>
        <div className="flex gap-1 mt-1" style={{ flexWrap: 'wrap' }}>
          {quickLocations.map((loc, index) => (
            <button
              key={index}
              className="badge badge-info"
              onClick={() => setQuickLocation(loc, true)}
              style={{ cursor: 'pointer', border: 'none', fontSize: '10px' }}
            >
              {loc.name}
            </button>
          ))}
        </div>
      </div>
      
      <div className="form-group">
        <label className="form-label">End Location</label>
        <div className="flex gap-1">
          <input
            type="number"
            step="0.0001"
            value={endLat}
            onChange={(e) => setEndLat(e.target.value)}
            className="form-input"
            placeholder="Latitude"
          />
          <input
            type="number"
            step="0.0001"
            value={endLon}
            onChange={(e) => setEndLon(e.target.value)}
            className="form-input"
            placeholder="Longitude"
          />
        </div>
        <div className="flex gap-1 mt-1" style={{ flexWrap: 'wrap' }}>
          {quickLocations.map((loc, index) => (
            <button
              key={index}
              className="badge badge-info"
              onClick={() => setQuickLocation(loc, false)}
              style={{ cursor: 'pointer', border: 'none', fontSize: '10px' }}
            >
              {loc.name}
            </button>
          ))}
        </div>
      </div>
      
      <div className="btn-group">
        <button
          className="btn btn-primary"
          onClick={handleCalculateRoute}
          disabled={loading}
        >
          {loading ? <div className="spinner"></div> : '🚀 Calculate Route'}
        </button>
        <button
          className="btn btn-outline"
          onClick={handleGetAlternatives}
          disabled={loading}
        >
          🔀 Alternatives
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          ❌ {error}
        </div>
      )}

      {result && (
        <div className="alert alert-success">
          <strong>✅ Route Calculated!</strong>
          <div className="stats-grid mt-2">
            <div className="stat-card">
              <div className="stat-value">{result.distance_km}</div>
              <div className="stat-label">Distance (km)</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{Math.round(result.estimated_time_min)}</div>
              <div className="stat-label">Time (min)</div>
            </div>
          </div>
          <div style={{ fontSize: '12px', marginTop: '8px', color: 'var(--text-secondary)' }}>
            <div>📍 Waypoints: {result.waypoints_count}</div>
            <div>🚗 Mode: {result.mode || mode}</div>
          </div>
        </div>
      )}

      {alternatives.length > 0 && (
        <div className="mt-2">
          <h4 style={{ fontSize: '14px', marginBottom: '8px', color: 'var(--text-primary)' }}>
            Alternative Routes ({alternatives.length})
          </h4>
          {alternatives.map((alt, index) => (
            <div 
              key={index}
              className="list-item"
              style={{ 
                background: 'var(--bg-secondary)',
                marginBottom: '8px',
                borderRadius: '8px',
                cursor: 'pointer'
              }}
              onClick={() => {
                setResult(alt);
                if (onRouteCalculated && alt.route) {
                  onRouteCalculated(alt.route);
                }
              }}
            >
              <div className="flex-between">
                <span style={{ fontWeight: '600' }}>Route {index + 1}</span>
                <span className="badge badge-info">{alt.mode}</span>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                📏 {alt.distance_km} km • ⏱️ {Math.round(alt.estimated_time_min)} min
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default RoutePanel;
'''

# Enhanced GeofencePanel
geofence_panel = '''import React, { useState } from 'react';
import axios from 'axios';

function GeofencePanel({ onLocationChecked, darkMode }) {
  const [lat, setLat] = useState('13.0200');
  const [lon, setLon] = useState('77.5680');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [campuses, setCampuses] = useState([]);

  const handleCheckGeofence = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/geofence', {
        lat: parseFloat(lat),
        lon: parseFloat(lon)
      });
      
      setResult(response.data);
      
      if (onLocationChecked) {
        onLocationChecked({ lat: parseFloat(lat), lon: parseFloat(lon), ...response.data });
      }
    } catch (err) {
      setError('Geofence check failed');
    } finally {
      setLoading(false);
    }
  };

  const handleUseCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLat(position.coords.latitude.toFixed(6));
          setLon(position.coords.longitude.toFixed(6));
        },
        (error) => {
          setError('Failed to get current location');
        }
      );
    } else {
      setError('Geolocation not supported by browser');
    }
  };

  const fetchCampuses = async () => {
    try {
      const response = await axios.get('/geofence');
      setCampuses(response.data.campuses || []);
    } catch (err) {
      console.error('Failed to fetch campuses:', err);
    }
  };

  React.useEffect(() => {
    fetchCampuses();
  }, []);

  const quickTestLocations = [
    { name: 'IISc (Inside)', lat: 13.0200, lon: 77.5680 },
    { name: 'Electronic City', lat: 12.8350, lon: 77.6650 },
    { name: 'Whitefield', lat: 12.9800, lon: 77.7500 },
    { name: 'Outside', lat: 12.9000, lon: 77.6000 },
  ];

  return (
    <div className="card">
      <h3 className="card-title">📍 Geofence Checker</h3>
      
      <div className="form-group">
        <label className="form-label">Test Location</label>
        <div className="flex gap-1">
          <input
            type="number"
            step="0.0001"
            value={lat}
            onChange={(e) => setLat(e.target.value)}
            className="form-input"
            placeholder="Latitude"
          />
          <input
            type="number"
            step="0.0001"
            value={lon}
            onChange={(e) => setLon(e.target.value)}
            className="form-input"
            placeholder="Longitude"
          />
        </div>
      </div>

      <div className="flex gap-1" style={{ flexWrap: 'wrap', marginBottom: '12px' }}>
        {quickTestLocations.map((loc, index) => (
          <button
            key={index}
            className="badge badge-info"
            onClick={() => {
              setLat(loc.lat.toString());
              setLon(loc.lon.toString());
            }}
            style={{ cursor: 'pointer', border: 'none', fontSize: '10px' }}
          >
            {loc.name}
          </button>
        ))}
      </div>
      
     <div className="btn-group">
        <button
          className="btn btn-primary"
          onClick={handleCheckGeofence}
          disabled={loading}
        >
          {loading ? <div className="spinner"></div> : '🔍 Check Location'}
        </button>
        <button
          className="btn btn-secondary"
          onClick={handleUseCurrentLocation}
        >
          📍 Use Current
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          ❌ {error}
        </div>
      )}

      {result && (
        <div className={`alert ${result.inside ? 'alert-success' : 'alert-warning'}`}>
          <strong>
            {result.inside ? '✅ Inside Geofence' : '⚠️ Outside Geofences'}
          </strong>
          {result.inside && (
            <>
              <div style={{ marginTop: '8px', fontSize: '14px' }}>
                <strong>📍 Campus:</strong> {result.campus}
              </div>
              {result.event && (
                <div className="mt-1">
                  <span className="badge badge-warning">{result.event} Event</span>
                </div>
              )}
            </>
          )}
          {!result.inside && result.nearest_campus && (
            <div style={{ marginTop: '8px', fontSize: '12px' }}>
              <div>Nearest: {result.nearest_campus}</div>
              <div>Distance: {result.distance_to_nearest_km.toFixed(2)} km</div>
            </div>
          )}
        </div>
      )}

      {campuses.length > 0 && (
        <div className="mt-2">
          <h4 style={{ fontSize: '14px', marginBottom: '8px', color: 'var(--text-primary)' }}>
            Campus Boundaries ({campuses.length})
          </h4>
          {campuses.map((campus, index) => (
            <div 
              key={index}
              className="list-item"
              style={{ 
                background: 'var(--bg-secondary)',
                marginBottom: '8px',
                borderRadius: '8px'
              }}
            >
              <div className="flex-between">
                <strong style={{ fontSize: '13px' }}>{campus.name}</strong>
                <span 
                  className="badge"
                  style={{ 
                     backgroundColor: campus.color + '33', 
                    color: campus.color 
                  }}
                >
                  {campus.type}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default GeofencePanel;
'''

# Enhanced GeocodePanel
geocode_panel = '''import React, { useState } from 'react';
import axios from 'axios';

function GeocodePanel({ darkMode }) {
  const [activeTab, setActiveTab] = useState('forward');
  
  // Forward geocoding state
  const [address, setAddress] = useState('MG Road, Bengaluru, Karnataka');
  const [forwardResult, setForwardResult] = useState(null);
  const [forwardLoading, setForwardLoading] = useState(false);
  
  // Reverse geocoding state
  const [lat, setLat] = useState('12.9716');
  const [lon, setLon] = useState('77.5946');
  const [reverseResult, setReverseResult] = useState(null);
  const [reverseLoading, setReverseLoading] = useState(false);
  
  // POI search state
  const [poiRadius, setPoiRadius] = useState('2');
  const [poiCategory, setPoiCategory] = useState('all');
  const [poiResults, setPoiResults] = useState([]);
  const [poiLoading, setPoiLoading] = useState(false);
  
  const [error, setError] = useState(null);

  const handleForwardGeocode = async () => {
    setFor wardLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/geocode', { address });
      setForwardResult(response.data);
    } catch (err) {
      setError('Geocoding failed');
    } finally {
      setForwardLoading(false);
    }
  };

  const handleReverseGeocode = async () => {
    setReverseLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/reverse-geocode', {
        lat: parseFloat(lat),
        lon: parseFloat(lon)
      });
      setReverseResult(response.data);
    } catch (err) {
      setError('Reverse geocoding failed');
    } finally {
      setReverseLoading(false);
    }
  };

  const handleSearchPOI = async () => {
    setPoiLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/poi/search', {
        lat: parseFloat(lat),
        lon: parseFloat(lon),
        radius_km: parseFloat(poiRadius),
        category: poiCategory
      });
      setPoiResults(response.data.pois || []);
    } catch (err) {
      setError('POI search failed');
    } finally {
      setPoiLoading(false);
    }
  };

  const famousPlaces = [
    'Cubbon Park, Bengaluru',
    'Lalbagh, Bengaluru',
    'MG Road, Bengaluru',
    'Whitefield, Bengaluru',
  ];

  return (
    <div className="card">
      <h3 className="card-title">🔍 Location Search</h3>
      
      <div style={{ 
        display: 'flex', 
        gap: '8px', 
        marginBottom: '16px',
        borderBottom: '2px solid var(--border-color)'
      }}>
        {['forward', 'reverse', 'poi'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              flex: 1,
              padding: '10px',
              border: 'none',
              background: activeTab === tab ? 'var(--primary-color)' : 'transparent',
              color: activeTab === tab ? 'white' : 'var(--text-secondary)',
              fontWeight: activeTab === tab ? '600' : '400',
              cursor: 'pointer',
              borderRadius: '6px 6px 0 0',
              transition: 'all 0.2s ease'
            }}
          >
            {tab === 'forward' && '📍 Address → GPS'}
            {tab === 'reverse' && '🔄 GPS → Address'}
            {tab === 'poi' && '🎯 Nearby POIs'}
          </button>
        ))}
      </div>

      {/* Forward Geocoding Tab */}
      {activeTab === 'forward' && (
        <>
          <div className="form-group">
            <label className="form-label">Enter Address</label>
            <input
              type="text"
              className="form-input"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Enter address"
            />
          </div>

          <div className="flex gap-1" style={{ flexWrap: 'wrap', marginBottom: '12px' }}>
            {famousPlaces.map((place, index) => (
              <button
                key={index}
                className="badge badge-info"
                onClick={() => setAddress(place)}
                style={{ cursor: 'pointer', border: 'none', fontSize: '10px' }}
              >
                {place.split(',')[0]}
              </button>
            ))}
          </div>

          <button
            className="btn btn-primary"
            onClick={handleForwardGeocode}
            disabled={forwardLoading}
          >
            {forwardLoading ? <div className="spinner"></div> : '🔍 Get Coordinates'}
          </button>

          {forwardResult && forwardResult.success && (
            <div className="alert alert-success">
              <strong>📍 Location Found!</strong>
              <div className="stats-grid mt-2">
                <div className="stat-card">
                  <div className="stat-value" style={{ fontSize: '16px' }}>
                    {forwardResult.latitude.toFixed(6)}
                  </div>
                  <div className="stat-label">Latitude</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value" style={{ fontSize: '16px' }}>
                    {forwardResult.longitude.toFixed(6)}
                  </div>
                  <div className="stat-label">Longitude</div>
                </div>
              </div>
              {forwardResult.display_name && (
                <div style={{ fontSize: '12px', marginTop: '8px', color: 'var(--text-secondary)' }}>
                  {forwardResult.display_name}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Reverse Geocoding Tab */}
      {activeTab === 'reverse' && (
        <>
          <div className="form-group">
            <label className="form-label">GPS Coordinates</label>
            <div className="flex gap-1">
              <input
                type="number"
                step="0.0001"
                className="form-input"
                value={lat}
                onChange={(e) => setLat(e.target.value)}
                placeholder="Latitude"
              />
              <input
                type="number"
                step="0.0001"
                className="form-input"
                value={lon}
                onChange={(e) => setLon(e.target.value)}
                placeholder="Longitude"
              />
            </div>
          </div>

          <button
            className="btn btn-primary"
            onClick={handleReverseGeocode}
            disabled={reverseLoading}
          >
            {reverseLoading ? <div className="spinner"></div> : '🔍 Get Address'}
          </button>

          {reverseResult && reverseResult.success && (
            <div className="alert alert-success">
              <strong>📮 Address Found!</strong>
              <div style={{ marginTop: '12px', fontSize: '13px' }}>
                {reverseResult.display_name}
              </div>
              {reverseResult.address && (
                <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {reverseResult.address.city && <div>🏙️ City: {reverseResult.address.city}</div>}
                  {reverseResult.address.postcode && <div>📬 Postcode: {reverseResult.address.postcode}</div>}
                  {reverseResult.address.road && <div>🛣️ Road: {reverseResult.address.road}</div>}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* POI Search Tab */}
      {activeTab === 'poi' && (
        <>
          <div className="form-group">
            <label className="form-label">Search Center</label>
            <div className="flex gap-1">
              <input
                type="number"
                step="0.0001"
                className="form-input"
                value={lat}
                onChange={(e) => setLat(e.target.value)}
                placeholder="Latitude"
              />
              <input
                type="number"
                step="0.0001"
                className="form-input"
                value={lon}
                onChange={(e) => setLon(e.target.value)}
                placeholder="Longitude"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Search Radius (km)</label>
            <input
              type="number"
              step="0.1"
              className="form-input"
              value={poiRadius}
              onChange={(e) => setPoiRadius(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Category</label>
            <select 
              className="form-input"
              value={poiCategory}
              onChange={(e) => setPoiCategory(e.target.value)}
            >
              <option value="all">All Categories</option>
              <option value="restaurant">Restaurants</option>
              <option value="shopping">Shopping</option>
              <option value="park">Parks</option>
              <option value="religious">Religious</option>
              <option value="tourist">Tourist Spots</option>
            </select>
          </div>

          <button
            className="btn btn-primary"
            onClick={handleSearchPOI}
            disabled={poiLoading}
          >
            {poiLoading ? <div className="spinner"></div> : '🎯 Search POIs'}
          </button>

          {poiResults.length > 0 && (
            <div className="mt-2">
              <h4 style={{ fontSize: '14px', marginBottom: '8px', color: 'var(--text-primary)' }}>
                Found {poiResults.length} Places
              </h4>
              {poiResults.map((poi, index) => (
                <div 
                  key={index}
                  className="list-item"
                  style={{ 
                    background: 'var(--bg-secondary)',
                    marginBottom: '8px',
                    borderRadius: '8px'
                  }}
                >
                  <div className="flex-between mb-1">
                    <strong>{poi.name}</strong>
                    <span className="badge badge-info">{poi.distance_km} km</span>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    <div>📍 {poi.lat.toFixed(4)}, {poi.lon.toFixed(4)}</div>
                    <div>🏷️ {poi.type}</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {poiResults.length === 0 && !poiLoading && (
            <div className="alert alert-info mt-2">
              Click "Search POIs" to find nearby places
            </div>
          )}
        </>
      )}

      {error && (
        <div className="alert alert-error">
          ❌ {error}
        </div>
      )}
    </div>
  );
}

export default GeocodePanel;
'''

print("Updating existing components...")

with open("frontend/src/components/RoutePanel.jsx", "w", encoding="utf-8") as f:
    f.write(route_panel)

with open("frontend/src/components/GeofencePanel.jsx", "w", encoding="utf-8") as f:
    f.write(geofence_panel)

with open("frontend/src/components/GeocodePanel.jsx", "w", encoding="utf-8") as f:
    f.write(geocode_panel)

print("✅ Existing components updated!")
print("   - RoutePanel.jsx (with alternatives, quick locations)")
print("   - GeofencePanel.jsx (with campus list)")
print("   - GeocodePanel.jsx (with POI search tab)")
