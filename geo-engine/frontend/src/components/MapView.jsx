import React, { useEffect, useState, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Polyline, Polygon, Marker, Popup, Circle, CircleMarker, useMap, GeoJSON } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Tamil Nadu center
const TAMILNADU_CENTER = [10.7905, 78.6547];
const TAMILNADU_ZOOM   = 7;

// Simplified Tamil Nadu boundary polygon (clockwise, ~50 control points)
const TAMILNADU_BOUNDARY = [
  [13.4200, 80.1300], [13.3200, 80.2500], [13.1700, 80.2800],
  [12.9500, 80.2400], [12.7800, 80.2600], [12.6000, 80.1600],
  [12.4000, 80.0800], [12.2400, 79.9200], [12.1100, 79.8500],
  [11.9400, 79.8200], [11.7500, 79.8500], [11.6200, 79.7600],
  [11.4800, 79.7700], [11.3300, 79.8500], [11.1500, 79.8300],
  [10.9800, 79.8500], [10.7800, 79.8400], [10.6000, 79.7800],
  [10.4200, 79.6900], [10.2500, 79.6200], [10.0800, 79.5500],
  [ 9.9300, 79.4200], [ 9.7800, 79.3200], [ 9.5500, 79.2300],
  [ 9.3500, 79.1800], [ 9.1600, 79.0700], [ 9.0000, 78.8800],
  [ 8.9000, 78.6000], [ 8.7400, 78.4200], [ 8.5500, 78.1500],
  [ 8.3300, 77.9000], [ 8.2500, 77.6500], [ 8.1500, 77.5500],
  [ 8.2200, 77.3500], [ 8.4900, 77.1500], [ 8.7000, 77.1000],
  [ 8.9500, 77.0500], [ 9.1500, 77.0800], [ 9.4700, 76.9500],
  [ 9.7800, 76.9300], [10.0500, 76.9500], [10.2700, 76.9600],
  [10.4800, 77.0500], [10.6200, 77.1500], [10.8600, 77.0800],
  [11.0000, 76.9700], [11.1500, 76.8800], [11.3000, 76.7000],
  [11.4700, 76.6200], [11.6500, 76.5800], [11.8000, 76.5500],
  [11.9500, 76.5800], [12.1000, 76.5500], [12.2300, 76.5500],
  [12.4000, 76.7000], [12.5500, 76.9200], [12.7000, 77.0200],
  [12.7800, 77.1200], [12.9500, 77.2500], [13.0000, 77.4400],
  [13.0400, 77.5500], [13.2300, 77.7000], [13.3500, 77.8600],
  [13.4200, 78.1200], [13.4800, 78.5000], [13.5800, 78.9200],
  [13.5500, 79.3500], [13.5000, 79.7000], [13.4200, 80.1300],
];

// ── Dark mode tile filter ──────────────────────────────────────────────────
function MapThemeController({ darkMode }) {
  const map = useMap();
  useEffect(() => {
    const tiles = document.querySelectorAll('.leaflet-tile-pane');
    tiles.forEach(tile => {
      tile.style.filter = darkMode ? 'invert(1) hue-rotate(180deg) brightness(0.9)' : 'none';
    });
  }, [darkMode, map]);
  return null;
}

// ── Fly to a position smoothly ─────────────────────────────────────────────
function FlyToLocation({ position, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (position) {
      map.flyTo(position, zoom || 14, { duration: 1.5 });
    }
  }, [position, zoom, map]);
  return null;
}

// ── Auto-fit map to the route bounds ───────────────────────────────────────
function FitBounds({ routes, routeCoords }) {
  const map = useMap();
  useEffect(() => {
    try {
      let coords = [];
      if (routes && routes.length > 0) {
        routes.forEach(r => {
          if (r.route) coords.push(...r.route);
        });
      } else if (routeCoords && routeCoords.length > 0) {
        coords = [...routeCoords];
      }
      
      if (coords.length > 1) {
        const bounds = L.latLngBounds(coords);
        if (bounds.isValid()) {
          map.flyToBounds(bounds, { padding: [50, 50], duration: 1.5 });
        }
      }
    } catch (e) {}
  }, [routes, routeCoords, map]);
  return null;
}

// ── Pulsing "You are here" CSS injected once ───────────────────────────────
const pulseStyle = `
  @keyframes geo-pulse {
    0%   { transform: scale(1);   opacity: 1; }
    70%  { transform: scale(2.5); opacity: 0; }
    100% { transform: scale(1);   opacity: 0; }
  }
  .geo-pulse-ring {
    position: absolute; top: 0; left: 0;
    width: 24px; height: 24px;
    border-radius: 50%;
    background: rgba(33, 150, 243, 0.45);
    animation: geo-pulse 1.8s ease-out infinite;
  }
  .geo-dot {
    position: relative;
    width: 24px; height: 24px;
    border-radius: 50%;
    background: #2196F3;
    border: 3px solid #fff;
    box-shadow: 0 2px 8px rgba(0,0,0,0.35);
  }
`;
if (!document.getElementById('geo-pulse-style')) {
  const s = document.createElement('style');
  s.id = 'geo-pulse-style';
  s.textContent = pulseStyle;
  document.head.appendChild(s);
}

const myLocationIcon = L.divIcon({
  className: '',
  html: `<div style="position:relative;width:24px;height:24px">
           <div class="geo-pulse-ring"></div>
           <div class="geo-dot"></div>
         </div>`,
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});

function MapView({ routeCoords, routes, gpsPoints, darkMode, trafficData, liveAssets,
                   measurePoints, userLocation, onUserLocation, anomalies }) {
  const [campuses, setCampuses] = useState([]);

  // Fetch Tamil Nadu campuses from backend
  useEffect(() => {
    fetch('/geofence')
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data?.campuses)) setCampuses(data.campuses);
      })
      .catch(() => {});
  }, []);

  // Route colour by safety score
  const routeColor = (route) => {
    if (!route?.safety_score) return '#2196F3';
    const s = route.safety_score;
    if (s >= 7) return '#4CAF50';
    if (s >= 4) return '#FF9800';
    return '#F44336';
  };

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
      center={TAMILNADU_CENTER}
      zoom={TAMILNADU_ZOOM}
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

      {/* Fly to user location when it changes */}
      {userLocation && <FlyToLocation position={[userLocation.lat, userLocation.lng]} zoom={14} />}

      {/* Auto-fit bounds for newly calculated routes */}
      <FitBounds routes={routes} routeCoords={routeCoords} />

      {/* Tamil Nadu state boundary */}
      <Polygon
        positions={TAMILNADU_BOUNDARY}
        pathOptions={{
          color: '#E53935',
          weight: 2.5,
          opacity: 0.75,
          fillColor: '#EF9A9A',
          fillOpacity: 0.08,
          dashArray: '6, 4',
        }}
      >
        <Popup>
          <div style={{ fontWeight: 'bold', fontSize: '13px' }}>
            🗺️ Tamil Nadu
          </div>
          <div style={{ fontSize: '11px', color: '#666' }}>
            Area: 130,058 km²<br />
            Districts: 38
          </div>
        </Popup>
      </Polygon>

      {/* User's current location */}
      {userLocation && (
        <>
          <Circle
            center={[userLocation.lat, userLocation.lng]}
            radius={userLocation.accuracy || 50}
            pathOptions={{
              color: '#2196F3',
              fillColor: '#2196F3',
              fillOpacity: 0.12,
              weight: 1.5,
            }}
          />
          <Marker
            position={[userLocation.lat, userLocation.lng]}
            icon={myLocationIcon}
            zIndexOffset={1000}
          >
            <Popup>
              <div>
                <strong>📍 Your Location</strong><br />
                <span style={{ fontSize: '11px', color: '#555' }}>
                  {userLocation.lat.toFixed(6)}, {userLocation.lng.toFixed(6)}
                </span><br />
                {userLocation.accuracy && (
                  <span style={{ fontSize: '11px', color: '#888' }}>
                    Accuracy: ±{Math.round(userLocation.accuracy)} m
                  </span>
                )}
              </div>
            </Popup>
          </Marker>
        </>
      )}
      
      {/* Campus Boundaries */}
      {campuses.map((campus) => (
        <Polygon
          key={campus.id}
          positions={campus.coordinates}
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
              <span style={{ fontSize: '11px', color: '#666' }}>{campus.type}</span>
            </div>
          </Popup>
        </Polygon>
      ))}

      {/* Multi-route alternatives */}
      {routes && routes.map((route, idx) => (
        route.route && route.route.length > 0 && (
          <Polyline
            key={`alt-${idx}`}
            positions={route.route}
            pathOptions={{
              color: routeColor(route),
              weight: idx === 0 ? 6 : 4,
              opacity: idx === 0 ? 0.9 : 0.55,
              dashArray: idx === 0 ? '' : '8, 6',
            }}
          >
            <Popup>
              <div>
                <strong>{route.label || `Route ${idx + 1}`}</strong><br />
                🕐 ETA: {Math.round(route.eta_min || route.duration_min || 0)} min<br />
                📏 {(route.distance_km || 0).toFixed(1)} km<br />
                {route.safety_score != null && (
                  <span>🛡️ Safety: {route.safety_score}/10</span>
                )}
              </div>
            </Popup>
          </Polyline>
        )
      ))}

      {/* Single route (legacy / non-multi mode) */}
      {!routes && routeCoords && routeCoords.length > 0 && (
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

      {/* Anomaly Markers */}
      {anomalies && anomalies.map((a, idx) => (
        <CircleMarker
          key={`anomaly-${idx}`}
          center={[a.lat, a.lon]}
          radius={10}
          pathOptions={{ color: '#F44336', fillColor: '#FF5722', fillOpacity: 0.85, weight: 2 }}
        >
          <Popup>
            <div>
              <strong>⚠️ Traffic Anomaly</strong><br />
              <span style={{ fontSize: '12px' }}>
                Asset: {a.asset_id || 'Unknown'}<br />
                Speed: {a.speed_kmh ? `${a.speed_kmh.toFixed(1)} km/h` : '—'}<br />
                {a.reason && <span>Reason: {a.reason}<br /></span>}
                {a.detected_at && <span>{new Date(a.detected_at).toLocaleTimeString()}</span>}
              </span>
            </div>
          </Popup>
        </CircleMarker>
      ))}

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
