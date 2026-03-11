"""
Frontend Enhancement Script for GeoEngine
Creates modern, feature-rich React components
"""

import os

# Enhanced App.js with dark mode and new layout
app_enhanced = '''import React, { useState, useEffect } from 'react';
import MapView from './components/MapView';
import RoutePanel from './components/RoutePanel';
import GeofencePanel from './components/GeofencePanel';
import GeocodePanel from './components/GeocodePanel';
import TrafficPanel from './components/TrafficPanel';
import AnalyticsPanel from './components/AnalyticsPanel';
import AssetTracker from './components/AssetTracker';
import FavoritesPanel from './components/FavoritesPanel';
import MeasurePanel from './components/MeasurePanel';
import './App.css';

function App() {
  const [routeCoords, setRouteCoords] = useState(null);
  const [gpsPoints, setGpsPoints] = useState([]);
  const [darkMode, setDarkMode] = useState(false);
  const [activeTab, setActiveTab] = useState('route');
  const [trafficData, setTrafficData] = useState([]);
  const [liveAssets, setLiveAssets] = useState([]);
  const [measurePoints, setMeasurePoints] = useState([]);

  // Apply dark mode class to body
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, [darkMode]);

  const handleRouteCalculated = (route) => {
    setRouteCoords(route);
  };

  const handleLocationChecked = (location) => {
    setGpsPoints([...gpsPoints, location]);
  };

  const handleTrafficUpdate = (traffic) => {
    setTrafficData(traffic);
  };

  const handleMeasureUpdate = (points) => {
    setMeasurePoints(points);
  };

  const renderActivePanel = () => {
    switch(activeTab) {
      case 'route':
        return <RoutePanel onRouteCalculated={handleRouteCalculated} darkMode={darkMode} />;
      case 'geofence':
        return <GeofencePanel onLocationChecked={handleLocationChecked} darkMode={darkMode} />;
      case 'geocode':
        return <GeocodePanel darkMode={darkMode} />;
      case 'traffic':
        return <TrafficPanel onTrafficUpdate={handleTrafficUpdate} darkMode={darkMode} />;
      case 'analytics':
        return <AnalyticsPanel darkMode={darkMode} />;
      case 'assets':
        return <AssetTracker onAssetsUpdate={setLiveAssets} darkMode={darkMode} />;
      case 'favorites':
        return <FavoritesPanel onRouteCalculated={handleRouteCalculated} darkMode={darkMode} />;
      case 'measure':
        return <MeasurePanel onMeasureUpdate={handleMeasureUpdate} darkMode={darkMode} />;
      default:
        return <RoutePanel onRouteCalculated={handleRouteCalculated} darkMode={darkMode} />;
    }
  };

  return (
    <div className={`App ${darkMode ? 'dark-mode' : ''}`}>
      <header className="app-header">
        <div className="header-content">
          <div className="header-title">
            <h1>🌍 GeoEngine</h1>
            <p>Intelligent Geospatial Platform - Bengaluru, India</p>
          </div>
          <button 
            className="theme-toggle"
            onClick={() => setDarkMode(!darkMode)}
            title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {darkMode ? '☀️' : '🌙'}
          </button>
        </div>
      </header>

      <div className="app-content">
        <aside className="sidebar">
          <nav className="tab-navigation">
            <button 
              className={`tab-button ${activeTab === 'route' ? 'active' : ''}`}
              onClick={() => setActiveTab('route')}
            >
              🗺️ Route
            </button>
            <button 
              className={`tab-button ${activeTab === 'geofence' ? 'active' : ''}`}
              onClick={() => setActiveTab('geofence')}
            >
              📍 Geofence
            </button>
            <button 
              className={`tab-button ${activeTab === 'geocode' ? 'active' : ''}`}
              onClick={() => setActiveTab('geocode')}
            >
              🔍 Search
            </button>
            <button 
              className={`tab-button ${activeTab === 'traffic' ? 'active' : ''}`}
              onClick={() => setActiveTab('traffic')}
            >
              🚦 Traffic
            </button>
            <button 
              className={`tab-button ${activeTab === 'analytics' ? 'active' : ''}`}
              onClick={() => setActiveTab('analytics')}
            >
              📊 Analytics
            </button>
            <button 
              className={`tab-button ${activeTab === 'assets' ? 'active' : ''}`}
              onClick={() => setActiveTab('assets')}
            >
              📡 Assets
            </button>
            <button 
              className={`tab-button ${activeTab === 'favorites' ? 'active' : ''}`}
              onClick={() => setActiveTab('favorites')}
            >
              ⭐ Favorites
            </button>
            <button 
              className={`tab-button ${activeTab === 'measure' ? 'active' : ''}`}
              onClick={() => setActiveTab('measure')}
            >
              📏 Measure
            </button>
          </nav>

          <div className="panel-container">
            {renderActivePanel()}
          </div>
        </aside>

        <main className="map-container">
          <MapView 
            routeCoords={routeCoords}
            gpsPoints={gpsPoints}
            darkMode={darkMode}
            trafficData={trafficData}
            liveAssets={liveAssets}
            measurePoints={measurePoints}
          />
        </main>
      </div>
    </div>
  );
}

export default App;
'''

# Enhanced App.css with modern styling
app_css = '''/* GeoEngine Enhanced Styles */

:root {
  --primary-color: #2196F3;
  --primary-dark: #1976D2;
  --primary-light: #64B5F6;
  --secondary-color: #4CAF50;
  --danger-color: #F44336;
  --warning-color: #FF9800;
  --text-primary: #212121;
  --text-secondary: #757575;
  --bg-primary: #FFFFFF;
  --bg-secondary: #F5F5F5;
  --border-color: #E0E0E0;
  --shadow: 0 2px 8px rgba(0,0,0,0.1);
  --shadow-hover: 0 4px 12px rgba(0,0,0,0.15);
}

.dark-mode {
  --primary-color: #42A5F5;
  --primary-dark: #1E88E5;
  --primary-light: #64B5F6;
  --text-primary: #FFFFFF;
  --text-secondary: #B0B0B0;
  --bg-primary: #1E1E1E;
  --bg-secondary: #2D2D2D;
  --border-color: #404040;
  --shadow: 0 2px 8px rgba(0,0,0,0.3);
  --shadow-hover: 0 4px 12px rgba(0,0,0,0.4);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: var(--bg-secondary);
  color: var(--text-primary);
  transition: background-color 0.3s ease, color 0.3s ease;
}

.App {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
  color: white;
  padding: 12px 20px;
  box-shadow: var(--shadow);
  z-index: 1000;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title h1 {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 2px;
}

.header-title p {
  font-size: 13px;
  opacity: 0.9;
}

.theme-toggle {
  background: rgba(255,255,255,0.2);
  border: none;
  color: white;
  font-size: 20px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.theme-toggle:hover {
  background: rgba(255,255,255,0.3);
  transform: scale(1.1);
}

.app-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar {
  width: 360px;
  background: var(--bg-primary);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.tab-navigation {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
  background: var(--bg-secondary);
  border-bottom: 2px solid var(--border-color);
  padding: 8px;
}

.tab-button {
  background: transparent;
  border: none;
  padding: 10px 8px;
  font-size: 11px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 6px;
  font-weight: 500;
  white-space: nowrap;
}

.tab-button:hover {
  background: var(--primary-light);
  color: white;
}

.tab-button.active {
  background: var(--primary-color);
  color: white;
  font-weight: 600;
}

.panel-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.panel-container::-webkit-scrollbar {
  width: 8px;
}

.panel-container::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

.panel-container::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

.panel-container::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}

.map-container {
  flex: 1;
  position: relative;
  background: var(--bg-secondary);
}

/* Card Styles */
.card {
  background: var(--bg-primary);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: var(--shadow);
  transition: all 0.3s ease;
  border: 1px solid var(--border-color);
}

.card:hover {
  box-shadow: var(--shadow-hover);
  transform: translateY(-2px);
}

.card-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Form Styles */
.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1.5px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: all 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
}

.form-input:disabled {
  background: var(--bg-secondary);
  cursor: not-allowed;
}

/* Button Styles */
.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-dark);
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}

.btn-secondary {
  background: var(--secondary-color);
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #45a049;
  transform: translateY(-2px);
}

.btn-danger {
  background: var(--danger-color);
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #d32f2f;
}

.btn-outline {
  background: transparent;
  color: var(--primary-color);
  border: 2px solid var(--primary-color);
}

.btn-outline:hover:not(:disabled) {
  background: var(--primary-color);
  color: white;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.btn-group {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

/* Alert/Result Styles */
.alert {
  padding: 12px 16px;
  border-radius: 8px;
  margin-top: 16px;
  font-size: 14px;
  border-left: 4px solid;
}

.alert-success {
  background: rgba(76, 175, 80, 0.1);
  border-color: var(--secondary-color);
  color: var(--secondary-color);
}

.alert-error {
  background: rgba(244, 67, 54, 0.1);
  border-color: var(--danger-color);
  color: var(--danger-color);
}

.alert-info {
  background: rgba(33, 150, 243, 0.1);
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.alert-warning {
  background: rgba(255, 152, 0, 0.1);
  border-color: var(--warning-color);
  color: var(--warning-color);
}

/* Loading Spinner */
.spinner {
  border: 3px solid var(--bg-secondary);
  border-top: 3px solid var(--primary-color);
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Badge Styles */
.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  margin: 4px;
}

.badge-success { background: rgba(76, 175, 80, 0.2); color: var(--secondary-color); }
.badge-danger { background: rgba(244, 67, 54, 0.2); color: var(--danger-color); }
.badge-warning { background: rgba(255, 152, 0, 0.2); color: var(--warning-color); }
.badge-info { background: rgba(33, 150, 243, 0.2); color: var(--primary-color); }

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin: 16px 0;
}

.stat-card {
  background: var(--bg-secondary);
  padding: 16px;
  border-radius: 10px;
  text-align: center;
  border: 1px solid var(--border-color);
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* List Styles */
.list-item {
  padding: 12px;
  border-bottom: 1px solid var(--border-color);
  transition: background 0.2s ease;
  cursor: pointer;
}

.list-item:hover {
  background: var(--bg-secondary);
}

.list-item:last-child {
  border-bottom: none;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .sidebar {
    width: 320px;
  }
  
  .tab-navigation {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .app-content {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    max-height: 50vh;
  }
  
  .map-container {
    height: 50vh;
  }
  
  .tab-navigation {
    grid-template-columns: repeat(4, 1fr);
  }
  
  .tab-button {
    font-size: 10px;
    padding: 8px 4px;
  }
}

/* Utility Classes */
.text-center { text-align: center; }
.text-right { text-align: right; }
.mt-1 { margin-top: 8px; }
.mt-2 { margin-top: 16px; }
.mb-1 { margin-bottom: 8px; }
.mb-2 { margin-bottom: 16px; }
.flex { display: flex; }
.flex-between { display: flex; justify-content: space-between; align-items: center; }
.flex-center { display: flex; justify-content: center; align-items: center; }
.gap-1 { gap: 8px; }
.gap-2 { gap: 16px; }
'''

print("Creating enhanced frontend files...")

os.makedirs("frontend/src", exist_ok=True)
os.makedirs("frontend/src/components", exist_ok=True)

with open("frontend/src/App.js", "w", encoding="utf-8") as f:
    f.write(app_enhanced)

with open("frontend/src/App.css", "w", encoding="utf-8") as f:
    f.write(app_css)

print("✅ Enhanced App.js and App.css created!")
print("   - Dark mode support")
print("   - Tabbed navigation")
print("   - Modern UI components")
