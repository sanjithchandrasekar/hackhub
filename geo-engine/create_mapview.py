"""
Create enhanced MapView component with all features
- Traffic heatmap visualization
- Live asset tracking
- Measurement points and lines
- Campus boundaries
- Route visualization
- Dark mode support
"""

import os

mapview_enhanced = '''import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Polyline, Polygon, Marker, Popup, Circle, CircleMarker, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const BENGALURU_CENTER = [12.9716, 77.5946];

// Custom component to handle map theme changes
function MapThemeController({ darkMode }) {
  const map = useMap();
  
  useEffect(() => {
    const tiles = document.querySelectorAll('.leaflet-tile-pane');
    tiles.forEach(tile => {
      if (darkMode) {
        tile.style.filter = 'invert(1) hue-rotate(180deg) brightness(0.9)';
      } else {
        tile.style.filter = 'none';
      }
    });
  }, [darkMode, map]);
  
  return null;
}

function MapView({ routeCoords, gpsPoints, darkMode, trafficData, liveAssets, measurePoints }) {
  const [campuses, setCampuses] = useState([
    {
      name: "IISc Campus",
      color: "#4CAF50",
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
      color: "#2196F3",
      coords: [
        [12.8400, 77.6600],
        [12.8400, 77.6700],
        [12.8300, 77.6700],
        [12.8300, 77.6600],
        [12.8400, 77.6600]
      ]
    },
    {
      name: "Whitefield",
      color: "#FF9800",
      coords: [
        [12.9850, 77.7450],
        [12.9850, 77.7550],
        [12.9750, 77.7550],
        [12.9750, 77.7450],
        [12.9850, 77.7450]
      ]
    }
  ]);

  // Create colored markers for assets based on status
  const createAssetIcon = (status) => {
    let color = '#2196F3';
    if (status === 'MOVING') color = '#4CAF50';
    if (status === 'IDLE') color = '#FF9800';
    if (status === 'SPEEDING') color = '#F44336';
    
    return L.divIcon({
      className: 'custom-asset-marker',
      html: `
        <div style="
          background: ${color};
          width: 24px;
          height: 24px;
          border-radius: 50%;
          border: 3px solid white;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
          font-size: 10px;
        ">
          🚗
        </div>
      `,
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });
  };

  // Create traffic heatmap marker
  const createTrafficIcon = (intensity) => {
    let color = '#4CAF50';
    if (intensity > 0.7) color = '#F44336';
    else if (intensity > 0.4) color = '#FF9800';
    
    const size = 20 + (intensity * 30);
    
    return L.divIcon({
      className: 'traffic-marker',
      html: `
        <div style="
          background: ${color};
          width: ${size}px;
          height: ${size}px;
          border-radius: 50%;
          opacity: 0.6;
          border: 2px solid ${color};
        "></div>
      `,
      iconSize: [size, size],
      iconAnchor: [size/2, size/2]
    });
  };

  return (
    <MapContainer
      center={BENGALURU_CENTER}
      zoom={12}
      style={{ height: '100%', width: '100%' }}
      zoomControl={true}
    >
      {/* Base Map Tiles */}
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      
      {/* Dark Mode Controller */}
      <MapThemeController darkMode={darkMode} />
      
      {/* Campus Boundaries */}
      {campuses.map((campus, index) => (
        <Polygon
          key={index}
          positions={campus.coords}
          pathOptions={{
            color: campus.color,
            fillColor: campus.color,
            fillOpacity: 0.15,
            weight: 3,
            dashArray: '10, 10'
          }}
        >
          <Popup>
            <div>
              <strong>{campus.name}</strong>
              <br />
              <span style={{ fontSize: '11px', color: '#666' }}>Campus Boundary</span>
            </div>
          </Popup>
        </Polygon>
      ))}

      {/* Route Visualization */}
      {routeCoords && routeCoords.length > 0 && (
        <>
          <Polyline
            positions={routeCoords}
            pathOptions={{
              color: '#2196F3',
              weight: 5,
              opacity: 0.8
            }}
          />
          
          {/* Start Marker */}
          <Marker position={routeCoords[0]}>
            <Popup>
              <div>
                <strong>🏁 Start</strong>
                <br />
                {routeCoords[0][0].toFixed(4)}, {routeCoords[0][1].toFixed(4)}
              </div>
            </Popup>
          </Marker>
          
          {/* End Marker */}
          <Marker position={routeCoords[routeCoords.length - 1]}>
            <Popup>
              <div>
                <strong>🎯 Destination</strong>
                <br />
                {routeCoords[routeCoords.length - 1][0].toFixed(4)}, {routeCoords[routeCoords.length - 1][1].toFixed(4)}
              </div>
            </Popup>
          </Marker>
        </>
      )}

      {/* GPS Points from Geofence Checks */}
      {gpsPoints && gpsPoints.map((point, index) => (
        <CircleMarker
          key={index}
          center={[point.lat, point.lon]}
          radius={8}
          pathOptions={{
            color: point.inside ? '#4CAF50' : '#F44336',
            fillColor: point.inside ? '#4CAF50' : '#F44336',
            fillOpacity: 0.7
          }}
        >
          <Popup>
            <div>
              <strong>{point.inside ? '✅ Inside Geofence' : '❌ Outside'}</strong>
              {point.campus && (
                <>
                  <br />
                  📍 {point.campus}
                </>
              )}
              <br />
              <span style={{ fontSize: '11px' }}>
                {point.lat.toFixed(4)}, {point.lon.toFixed(4)}
              </span>
            </div>
          </Popup>
        </CircleMarker>
      ))}

      {/* Traffic Heatmap */}
      {trafficData && trafficData.map((hotspot, index) => (
        <React.Fragment key={`traffic-${index}`}>
          <Circle
            center={[hotspot.lat, hotspot.lon]}
            radius={500 + (hotspot.intensity * 1000)}
            pathOptions={{
              color: hotspot.intensity > 0.7 ? '#F44336' : hotspot.intensity > 0.4 ? '#FF9800' : '#4CAF50',
              fillColor: hotspot.intensity > 0.7 ? '#F44336' : hotspot.intensity > 0.4 ? '#FF9800' : '#4CAF50',
              fillOpacity: 0.2,
              weight: 2,
              opacity: 0.5
            }}
          />
          <Marker
            position={[hotspot.lat, hotspot.lon]}
            icon={createTrafficIcon(hotspot.intensity)}
          >
            <Popup>
              <div>
                <strong>🚦 {hotspot.name}</strong>
                <br />
                <span style={{ fontSize: '12px' }}>
                  Intensity: {Math.round(hotspot.intensity * 100)}%
                  <br />
                  Vehicles: ~{hotspot.vehicles}
                  <br />
                  Avg Speed: {hotspot.avg_speed_kmh} km/h
                </span>
              </div>
            </Popup>
          </Marker>
        </React.Fragment>
      ))}

      {/* Live Asset Tracking */}
      {liveAssets && liveAssets.map((asset, index) => (
        <Marker
          key={`asset-${index}`}
          position={[asset.current_position.lat, asset.current_position.lon]}
          icon={createAssetIcon(asset.status)}
        >
          <Popup>
            <div>
              <strong>📡 {asset.asset_id}</strong>
              <br />
              <span style={{ fontSize: '12px' }}>
                Status: <strong>{asset.status}</strong>
                <br />
                Speed: {asset.speed.toFixed(1)} km/h
                <br />
                Heading: {asset.heading}°
                <br />
                Reports: {asset.total_reports}
                {asset.last_update && (
                  <>
                    <br />
                    Updated: {new Date(asset.last_update).toLocaleTimeString()}
                  </>
                )}
              </span>
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Measurement Points and Lines */}
      {measurePoints && measurePoints.length > 0 && (
        <>
          {/* Draw lines connecting measurement points */}
          {measurePoints.length > 1 && (
            <Polyline
              positions={measurePoints.map(p => [p.lat, p.lon])}
              pathOptions={{
                color: '#9C27B0',
                weight: 3,
                opacity: 0.7,
                dashArray: '10, 5'
              }}
            />
          )}
          
          {/* Draw markers for each measurement point */}
          {measurePoints.map((point, index) => (
            <CircleMarker
              key={`measure-${index}`}
              center={[point.lat, point.lon]}
              radius={6}
              pathOptions={{
                color: '#9C27B0',
                fillColor: '#9C27B0',
                fillOpacity: 1,
                weight: 2
              }}
            >
              <Popup>
                <div>
                  <strong>📏 Point {index + 1}</strong>
                  <br />
                  <span style={{ fontSize: '11px' }}>
                    {point.lat.toFixed(6)}, {point.lon.toFixed(6)}
                  </span>
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </>
      )}

      {/* Map Legend */}
      <div style={{
        position: 'absolute',
        bottom: '30px',
        right: '10px',
        background: darkMode ? 'rgba(30, 30, 30, 0.95)' : 'rgba(255, 255, 255, 0.95)',
        padding: '12px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
        zIndex: 1000,
        fontSize: '11px',
        color: darkMode ? '#fff' : '#333',
        maxWidth: '180px'
      }}>
        <div style={{ fontWeight: 'bold', marginBottom: '8px', fontSize: '12px' }}>
          🗺️ Map Legend
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
          <div style={{ width: '12px', height: '12px', background: '#2196F3', borderRadius: '50%', marginRight: '6px' }}></div>
          <span>Route</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
          <div style={{ width: '12px', height: '12px', background: '#4CAF50', borderRadius: '50%', marginRight: '6px' }}></div>
          <span>Moving Asset</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
          <div style={{ width: '12px', height: '12px', background: '#FF9800', borderRadius: '50%', marginRight: '6px' }}></div>
          <span>Idle Asset</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
          <div style={{ width: '12px', height: '12px', background: '#F44336', borderRadius: '50%', marginRight: '6px' }}></div>
          <span>Speeding Asset</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
          <div style={{ width: '12px', height: '12px', background: '#9C27B0', borderRadius: '50%', marginRight: '6px' }}></div>
          <span>Measurement</span>
        </div>
      </div>
    </MapContainer>
  );
}

export default MapView;
'''

print("Creating enhanced MapView...")

with open("frontend/src/components/MapView.jsx", "w", encoding="utf-8") as f:
    f.write(mapview_enhanced)

print("✅ Enhanced MapView created!")
print("   - Traffic heatmap visualization")
print("   - Live asset tracking with custom icons")
print("   - Measurement points and lines")
print("   - Campus boundaries")
print("   - Route visualization")
print("   - Dark mode support")
print("   - Interactive legend")
