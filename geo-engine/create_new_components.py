"""
Create NEW React components for enhanced features
- TrafficPanel
- AnalyticsPanel  
- AssetTracker
- FavoritesPanel
- MeasurePanel
"""

import os

# Traffic Panel Component
traffic_panel = '''import React, { useState, useEffect } from 'react';
import axios from 'axios';

function TrafficPanel({ onTrafficUpdate, darkMode }) {
  const [trafficData, setTrafficData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchTraffic = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/traffic/heatmap');
      setTrafficData(response.data);
      if (onTrafficUpdate) {
        onTrafficUpdate(response.data.hotspots);
      }
    } catch (error) {
      console.error('Failed to fetch traffic:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchTraffic, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  return (
    <div className="card">
      <h3 className="card-title">🚦 Live Traffic Heatmap</h3>
      
      <div className="btn-group">
        <button 
          className="btn btn-primary"
          onClick={fetchTraffic}
          disabled={loading}
        >
          {loading ? 'Loading...' : '🔄 Refresh Traffic'}
        </button>
        <button 
          className={`btn ${autoRefresh ? 'btn-secondary' : 'btn-outline'}`}
          onClick={() => setAutoRefresh(!autoRefresh)}
        >
          {autoRefresh ? '⏸️ Pause' : '▶️ Auto'}
        </button>
      </div>

      {trafficData && (
        <>
          <div className="alert alert-info mt-2">
            <small>Last updated: {new Date(trafficData.timestamp).toLocaleTimeString()}</small>
          </div>

          <div className="mt-2">
            <h4 style={{ fontSize: '14px', marginBottom: '12px', color: 'var(--text-primary)' }}>
              Traffic Hotspots ({trafficData.hotspots.length})
            </h4>
            
            {trafficData.hotspots.map((hotspot, index) => (
              <div 
                key={index}
                className="list-item"
                style={{ 
                  background: 'var(--bg-secondary)',
                  marginBottom: '8px',
                  borderRadius: '8px'
                }}
              >
                <div style={{ fontWeight: '600', marginBottom: '4px' }}>
                  {hotspot.name}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  <div>📊 Intensity: {Math.round(hotspot.intensity * 100)}%</div>
                  <div>🚗 Vehicles: ~{hotspot.vehicles}</div>
                  <div>⚡ Avg Speed: {hotspot.avg_speed_kmh} km/h</div>
                </div>
                <div className="mt-1">
                  {hotspot.intensity > 0.7 ? (
                    <span className="badge badge-danger">Heavy Traffic</span>
                  ) : hotspot.intensity > 0.4 ? (
                    <span className="badge badge-warning">Moderate Traffic</span>
                  ) : (
                    <span className="badge badge-success">Light Traffic</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {!trafficData && !loading && (
        <div className="alert alert-info mt-2">
          Click "Refresh Traffic" to load current traffic conditions
        </div>
      )}
    </div>
  );
}

export default TrafficPanel;
'''

# Analytics Panel Component
analytics_panel = '''import React, { useState, useEffect } from 'react';
import axios from 'axios';

function AnalyticsPanel({ darkMode }) {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/analytics/routes');
      setAnalytics(response.data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  return (
    <div className="card">
      <h3 className="card-title">📊 Route Analytics</h3>
      
      <button 
        className="btn btn-primary"
        onClick={fetchAnalytics}
        disabled={loading}
      >
        {loading ? 'Loading...' : '🔄 Refresh Data'}
      </button>

      {analytics && (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{analytics.total_routes}</div>
              <div className="stat-label">Total Routes</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{analytics.avg_distance_km}</div>
              <div className="stat-label">Avg Distance (km)</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{Math.round(analytics.avg_time_min)}</div>
              <div className="stat-label">Avg Time (min)</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{analytics.recent_routes.length}</div>
              <div className="stat-label">Recent Routes</div>
            </div>
          </div>

          {analytics.recent_routes.length > 0 && (
            <div className="mt-2">
              <h4 style={{ fontSize: '14px', marginBottom: '12px', color: 'var(--text-primary)' }}>
                Recent Routes
              </h4>
              {analytics.recent_routes.slice(-5).reverse().map((route, index) => (
                <div 
                  key={index}
                  className="list-item"
                  style={{ 
                    background: 'var(--bg-secondary)',
                    marginBottom: '8px',
                    borderRadius: '8px'
                  }}
                >
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    <div>📏 Distance: {route.distance_km} km</div>
                    <div>⏱️ ETA: {Math.round(route.estimated_time_min)} min</div>
                    <div>🚗 Mode: {route.mode || 'fastest'}</div>
                    {route.timestamp && (
                      <div>🕐 Time: {new Date(route.timestamp).toLocaleTimeString()}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {analytics && analytics.total_routes === 0 && (
        <div className="alert alert-info mt-2">
          No route data available yet. Calculate some routes to see analytics!
        </div>
      )}
    </div>
  );
}

export default AnalyticsPanel;
'''

# Asset Tracker Component
asset_tracker = '''import React, { useState, useEffect } from 'react';
import axios from 'axios';

function AssetTracker({ onAssetsUpdate, darkMode }) {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchAssets = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/assets/live');
      setAssets(response.data.assets || []);
      if (onAssetsUpdate) {
        onAssetsUpdate(response.data.assets || []);
      }
    } catch (error) {
      console.error('Failed to fetch assets:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchAssets, 5000); // Refresh every 5 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getStatusColor = (status) => {
    switch(status) {
      case 'MOVING': return 'success';
      case 'IDLE': return 'warning';
      case 'SPEEDING': return 'danger';
      default: return 'info';
    }
  };

  return (
    <div className="card">
      <h3 className="card-title">📡 Live Asset Tracking</h3>
      
      <div className="flex-between mb-2">
        <div>
          <span className="badge badge-info">{assets.length} Active Assets</span>
        </div>
        <button 
          className={`btn ${autoRefresh ? 'btn-secondary' : 'btn-outline'}`}
          onClick={() => setAutoRefresh(!autoRefresh)}
          style={{ padding: '6px 12px', fontSize: '12px' }}
        >
          {autoRefresh ? '⏸️ Pause' : '▶️ Auto'}
        </button>
      </div>

      {loading && assets.length === 0 && (
        <div className="flex-center" style={{ padding: '20px' }}>
          <div className="spinner"></div>
        </div>
      )}

      {assets.length > 0 && (
        <div>
          {assets.map((asset, index) => (
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
                <strong style={{ fontSize: '14px' }}>{asset.asset_id}</strong>
                <span className={`badge badge-${getStatusColor(asset.status)}`}>
                  {asset.status}
                </span>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                <div>📍 Position: {asset.current_position?.lat.toFixed(4)}, {asset.current_position?.lon.toFixed(4)}</div>
                <div>⚡ Speed: {asset.speed.toFixed(1)} km/h</div>
                <div>🧭 Heading: {asset.heading}°</div>
                <div>📊 Reports: {asset.total_reports}</div>
                {asset.last_update && (
                  <div>🕐 Updated: {new Date(asset.last_update).toLocaleTimeString()}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {assets.length === 0 && !loading && (
        <div className="alert alert-info">
          No active assets. Start the telemetry simulator to see live tracking!
          <br/><br/>
          <code style={{ fontSize: '11px' }}>cd scripts && python simulate_telemetry.py</code>
        </div>
      )}
    </div>
  );
}

export default AssetTracker;
'''

# Favorites Panel Component
favorites_panel = '''import React, { useState, useEffect } from 'react';
import axios from 'axios';

function FavoritesPanel({ onRouteCalculated, darkMode }) {
  const [favorites, setFavorites] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    start_lat: '12.9716',
    start_lon: '77.5946',
    end_lat: '12.9350',
    end_lon: '77.6244',
    notes: ''
  });

  useEffect(() => {
    fetchFavorites();
  }, []);

  const fetchFavorites = async () => {
    try {
      const response = await axios.get('/favorites');
      setFavorites(response.data.favorites || []);
    } catch (error) {
      console.error('Failed to fetch favorites:', error);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/favorites', formData);
      setShowAddForm(false);
      setFormData({
        name: '',
        start_lat: '12.9716',
        start_lon: '77.5946',
        end_lat: '12.9350',
        end_lon: '77.6244',
        notes: ''
      });
      fetchFavorites();
    } catch (error) {
      console.error('Failed to add favorite:', error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`/favorites/${id}`);
      fetchFavorites();
    } catch (error) {
      console.error('Failed to delete favorite:', error);
    }
  };

  const handleLoadRoute = async (favorite) => {
    try {
      const response = await axios.post('/route', {
        start_lat: favorite.start_lat,
        start_lon: favorite.start_lon,
        end_lat: favorite.end_lat,
        end_lon: favorite.end_lon
      });
      if (onRouteCalculated && response.data.route) {
        onRouteCalculated(response.data.route);
      }
    } catch (error) {
      console.error('Failed to load route:', error);
    }
  };

  return (
    <div className="card">
      <h3 className="card-title">⭐ Favorite Routes</h3>
      
      <button 
        className="btn btn-primary"
        onClick={() => setShowAddForm(!showAddForm)}
      >
        {showAddForm ? '❌ Cancel' : '➕ Add Favorite'}
      </button>

      {showAddForm && (
        <form onSubmit={handleAdd} className="mt-2">
          <div className="form-group">
            <label className="form-label">Route Name</label>
            <input 
              type="text"
              className="form-input"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
              placeholder="e.g., Home to Office"
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">Start Lat / Lon</label>
            <div className="flex gap-1">
              <input 
                type="number"
                step="0.0001"
                className="form-input"
                value={formData.start_lat}
                onChange={(e) => setFormData({...formData, start_lat: e.target.value})}
                required
              />
              <input 
                type="number"
                step="0.0001"
                className="form-input"
                value={formData.start_lon}
                onChange={(e) => setFormData({...formData, start_lon: e.target.value})}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">End Lat / Lon</label>
            <div className="flex gap-1">
              <input 
                type="number"
                step="0.0001"
                className="form-input"
                value={formData.end_lat}
                onChange={(e) => setFormData({...formData, end_lat: e.target.value})}
                required
              />
              <input 
                type="number"
                step="0.0001"
                className="form-input"
                value={formData.end_lon}
                onChange={(e) => setFormData({...formData, end_lon: e.target.value})}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Notes (optional)</label>
            <input 
              type="text"
              className="form-input"
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              placeholder="Add notes..."
            />
          </div>

          <button type="submit" className="btn btn-secondary">
            💾 Save Favorite
          </button>
        </form>
      )}

      {favorites.length > 0 && (
        <div className="mt-2">
          {favorites.map((fav, index) => (
            <div 
              key={fav.id || index}
              className="list-item"
              style={{ 
                background: 'var(--bg-secondary)',
                marginBottom: '8px',
                borderRadius: '8px'
              }}
            >
              <div className="flex-between mb-1">
                <strong>{fav.name}</strong>
              </div>
              {fav.notes && (
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  {fav.notes}
                </div>
              )}
              <div className="flex gap-1">
                <button 
                  className="btn btn-outline"
                  style={{ padding: '6px 12px', fontSize: '12px' }}
                  onClick={() => handleLoadRoute(fav)}
                >
                  🗺️ Load Route
                </button>
                <button 
                  className="btn btn-danger"
                  style={{ padding: '6px 12px', fontSize: '12px' }}
                  onClick={() => handleDelete(fav.id)}
                >
                  🗑️ Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {favorites.length === 0 && !showAddForm && (
        <div className="alert alert-info mt-2">
          No saved routes yet. Add your frequently used routes as favorites!
        </div>
      )}
    </div>
  );
}

export default FavoritesPanel;
'''

# Measure Panel Component
measure_panel = '''import React, { useState } from 'react';
import axios from 'axios';

function MeasurePanel({ onMeasureUpdate, darkMode }) {
  const [points, setPoints] = useState([]);
  const [measureType, setMeasureType] = useState('distance');
  const [result, setResult] = useState(null);
  const [message, setMessage] = useState('');

  const addPoint = () => {
    const newPoint = {
      lat: 12.9716 + (Math.random() - 0.5) * 0.1,
      lon: 77.5946 + (Math.random() - 0.5) * 0.1
    };
    const newPoints = [...points, newPoint];
    setPoints(newPoints);
    if (onMeasureUpdate) {
      onMeasureUpdate(newPoints);
    }
  };

  const removePoint = (index) => {
    const newPoints = points.filter((_, i) => i !== index);
    setPoints(newPoints);
    if (onMeasureUpdate) {
      onMeasureUpdate(newPoints);
    }
    setResult(null);
  };

  const clearAll = () => {
    setPoints([]);
    setResult(null);
    if (onMeasureUpdate) {
      onMeasureUpdate([]);
    }
  };

  const calculate = async () => {
    if (measureType === 'distance' && points.length < 2) {
      setMessage('Add at least 2 points for distance measurement');
      return;
    }
    if (measureType === 'area' && points.length < 3) {
      setMessage('Add at least 3 points for area measurement');
      return;
    }

    try {
      const response = await axios.post('/measure', {
        points: points,
        measurement_type: measureType
      });
      setResult(response.data);
      setMessage('');
    } catch (error) {
      setMessage('Measurement failed');
      console.error(error);
    }
  };

  const updatePoint = (index, field, value) => {
    const newPoints = [...points];
    newPoints[index][field] = parseFloat(value) || 0;
    setPoints(newPoints);
    if (onMeasureUpdate) {
      onMeasureUpdate(newPoints);
    }
  };

  return (
    <div className="card">
      <h3 className="card-title">📏 Measurement Tools</h3>
      
      <div className="form-group">
        <label className="form-label">Measurement Type</label>
        <select 
          className="form-input"
          value={measureType}
          onChange={(e) => {
            setMeasureType(e.target.value);
            setResult(null);
          }}
        >
          <option value="distance">Distance (Path)</option>
          <option value="area">Area (Polygon)</option>
        </select>
      </div>

      <div className="btn-group">
        <button className="btn btn-primary" onClick={addPoint}>
          ➕ Add Point
        </button>
        <button className="btn btn-danger" onClick={clearAll} disabled={points.length === 0}>
          🗑️ Clear All
        </button>
      </div>

      {points.length > 0 && (
        <div className="mt-2">
          <h4 style={{ fontSize: '14px', marginBottom: '8px', color: 'var(--text-primary)' }}>
            Points ({points.length})
          </h4>
          {points.map((point, index) => (
            <div key={index} className="flex gap-1 mb-1" style={{ alignItems: 'center' }}>
              <span style={{ fontSize: '12px', minWidth: '20px' }}>{index + 1}.</span>
              <input 
                type="number"
                step="0.0001"
                className="form-input"
                value={point.lat}
                onChange={(e) => updatePoint(index, 'lat', e.target.value)}
                placeholder="Lat"
                style={{ fontSize: '12px' }}
              />
              <input 
                type="number"
                step="0.0001"
                className="form-input"
                value={point.lon}
                onChange={(e) => updatePoint(index, 'lon', e.target.value)}
                placeholder="Lon"
                style={{ fontSize: '12px' }}
              />
              <button 
                className="btn btn-danger"
                onClick={() => removePoint(index)}
                style={{ padding: '8px', fontSize: '12px' }}
              >
                ❌
              </button>
            </div>
          ))}
        </div>
      )}

      {points.length >= (measureType === 'area' ? 3 : 2) && (
        <button className="btn btn-secondary mt-2" onClick={calculate}>
          📐 Calculate {measureType === 'area' ? 'Area' : 'Distance'}
        </button>
      )}

      {result && result.type === 'distance' && (
        <div className="alert alert-success mt-2">
          <strong>📏 Total Distance:</strong><br/>
          {result.distance_km} km<br/>
          {result.distance_m} meters
        </div>
      )}

      {result && result.type === 'area' && (
        <div className="alert alert-success mt-2">
          <strong>📐 Total Area:</strong><br/>
          {result.area_km2} km²<br/>
          {result.area_m2} m²<br/>
          {result.area_hectares} hectares
        </div>
      )}

      {message && (
        <div className="alert alert-warning mt-2">
          {message}
        </div>
      )}

      {points.length === 0 && (
        <div className="alert alert-info mt-2">
          Add points to measure distance or area. You can manually edit coordinates or click on the map.
        </div>
      )}
    </div>
  );
}

export default MeasurePanel;
'''

print("Creating NEW component files...")

os.makedirs("frontend/src/components", exist_ok=True)

with open("frontend/src/components/TrafficPanel.jsx", "w", encoding="utf-8") as f:
    f.write(traffic_panel)

with open("frontend/src/components/Analyt icsPanel.jsx", "w", encoding="utf-8") as f:
    f.write(analytics_panel)

with open("frontend/src/components/AssetTracker.jsx", "w", encoding="utf-8") as f:
    f.write(asset_tracker)

with open("frontend/src/components/FavoritesPanel.jsx", "w", encoding="utf-8") as f:
    f.write(favorites_panel)

with open("frontend/src/components/MeasurePanel.jsx", "w", encoding="utf-8") as f:
    f.write(measure_panel)

print("✅ New components created!")
print("   - TrafficPanel.jsx")
print("   - AnalyticsPanel.jsx")
print("   - AssetTracker.jsx")
print("   - FavoritesPanel.jsx")
print("   - MeasurePanel.jsx")
