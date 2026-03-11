"""
Create Frontend App.js and index.js
"""

import os

def create_app_files():
    """Create App.js and index.js"""
    
    # Create App.js
    with open("frontend/src/App.js", "w", encoding="utf-8") as f:
        f.write('''/**
 * Main Application Component
 * GeoEngine - Bengaluru Geospatial Engine
 * 
 * Layout:
 * - Left sidebar (320px) with control panels
 * - Right side with interactive map
 * 
 * Features:
 * - Route planning
 * - Geofence checking
 * - Geocoding/reverse geocoding
 * - Real-time GPS visualization
 */

import React, { useState } from 'react';
import MapView from './components/MapView';
import RoutePanel from './components/RoutePanel';
import GeofencePanel from './components/GeofencePanel';
import GeocodePanel from './components/GeocodePanel';
import './App.css';

function App() {
  const [routeCoords, setRouteCoords] = useState(null);
  const [gpsPoints, setGpsPoints] = useState([]);

  const handleRouteCalculated = (route) => {
    setRouteCoords(route);
  };

  const handleLocationChecked = (location) => {
    setGpsPoints([...gpsPoints, location]);
  };

  return (
    <div className="App">
      {/* Header */}
      <header className="app-header">
        <h1>🌍 GeoEngine</h1>
        <p>Intelligent Geospatial Engine - Bengaluru, India</p>
      </header>

      {/* Main Content */}
      <div className="app-content">
        {/* Left Sidebar */}
        <aside className="sidebar">
          <RoutePanel onRouteCalculated={handleRouteCalculated} />
          <GeofencePanel onLocationChecked={handleLocationChecked} />
          <GeocodePanel />
        </aside>

        {/* Map Area */}
        <main className="map-container">
          <MapView 
            routeCoords={routeCoords} 
            gpsPoints={gpsPoints}
          />
        </main>
      </div>
    </div>
  );
}

export default App;
''')

    # Create index.js
    with open("frontend/src/index.js", "w", encoding="utf-8") as f:
        f.write('''/**
 * React Application Entry Point
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
''')

    # Create App.css
    with open("frontend/src/App.css", "w", encoding="utf-8") as f:
        f.write('''/* GeoEngine Application Styles */

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #f5f5f5;
}

.App {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
  color: white;
  padding: 15px 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  z-index: 1000;
}

.app-header h1 {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 4px;
}

.app-header p {
  font-size: 13px;
  opacity: 0.9;
}

.app-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar {
  width: 320px;
  background: #fafafa;
  overflow-y: auto;
  padding: 15px;
  border-right: 1px solid #e0e0e0;
}

.map-container {
  flex: 1;
  position: relative;
}

/* Scrollbar styling */
.sidebar::-webkit-scrollbar {
  width: 8px;
}

.sidebar::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.sidebar::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.sidebar::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* Responsive design */
@media (max-width: 768px) {
  .app-content {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    max-height: 40vh;
  }
  
  .map-container {
    height: 60vh;
  }
}
''')

    # Create index.css
    with open("frontend/src/index.css", "w", encoding="utf-8") as f:
        f.write('''body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
''')

    # Create public/index.html
    os.makedirs("frontend/public", exist_ok=True)
    with open("frontend/public/index.html", "w", encoding="utf-8") as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#2196F3" />
    <meta
      name="description"
      content="GeoEngine - Intelligent Geospatial Engine with Real-Time Learning"
    />
    <title>GeoEngine - Bengaluru</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
''')

    print("✅ Frontend App files created successfully!")
    print("   - App.js (Main application component)")
    print("   - index.js (React entry point)")
    print("   - App.css (Application styles)")
    print("   - index.css (Global styles)")
    print("   - public/index.html (HTML template)")

if __name__ == "__main__":
    create_app_files()
