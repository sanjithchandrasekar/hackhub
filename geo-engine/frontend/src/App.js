import React, { useState, useEffect } from 'react';
import MapView from './components/MapView';
import RoutePanel from './components/RoutePanel';
import GeofencePanel from './components/GeofencePanel';
import GeocodePanel from './components/GeocodePanel';
import AnalyticsPanel from './components/AnalyticsPanel';
import TrafficPanel from './components/TrafficPanel';
import AnomalyPanel from './components/AnomalyPanel';
import Navbar from './components/Navbar';
import { Toaster } from 'react-hot-toast';

function App() {
  const [routeCoords, setRouteCoords] = useState(null);
  const [routes, setRoutes] = useState(null);           // multi-route alternatives
  const [gpsPoints, setGpsPoints] = useState([]);
  const [darkMode, setDarkMode] = useState(false);
  const [activeTab, setActiveTab] = useState('route');
  const [trafficData, setTrafficData] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [liveAssets] = useState([]);
  const [measurePoints] = useState([]);
  const [userLocation, setUserLocation] = useState(null);
  const [locating, setLocating] = useState(false);
  const [locationError, setLocationError] = useState(null);
  const watchIdRef = React.useRef(null);

  // Apply dark mode class to body
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, [darkMode]);

  // Start watching geolocation
  const handleLocateMe = () => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser.');
      return;
    }
    setLocating(true);
    setLocationError(null);

    // Clear any existing watch
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
    }

    watchIdRef.current = navigator.geolocation.watchPosition(
      (pos) => {
        setUserLocation({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
        });
        setLocating(false);
        setLocationError(null);
      },
      (err) => {
        setLocating(false);
        setLocationError(
          err.code === 1 ? 'Location access denied. Please allow location in browser settings.'
          : err.code === 2 ? 'Position unavailable. Please check GPS.'
          : 'Location request timed out. Try again.'
        );
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 5000 }
    );
  };

  // Stop watching on unmount
  useEffect(() => {
    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, []);

  const handleRouteCalculated = (route) => {
    setRouteCoords(route);
  };

  const handleRoutesCalculated = (alts) => {
    setRoutes(alts);
    if (!alts) setRouteCoords(null);
  };

  const handleLocationChecked = (location) => {
    setGpsPoints([...gpsPoints, location]);
  };

  const renderPanel = () => {
    switch (activeTab) {
      case 'route':
        return <RoutePanel
          onRouteCalculated={handleRouteCalculated}
          onRoutesCalculated={handleRoutesCalculated}
          darkMode={darkMode}
        />;
      case 'geofence':  return <GeofencePanel onLocationChecked={handleLocationChecked} darkMode={darkMode} userLocation={userLocation} />;
      case 'geocode':   return <GeocodePanel darkMode={darkMode} />;
      case 'traffic':   return <TrafficPanel darkMode={darkMode} onHeatmapData={setTrafficData} />;
      case 'anomalies': return <AnomalyPanel darkMode={darkMode} onAnomaliesLoaded={setAnomalies} />;
      case 'analytics': return <AnalyticsPanel darkMode={darkMode} />;
      default:
        return <RoutePanel onRouteCalculated={handleRouteCalculated} onRoutesCalculated={handleRoutesCalculated} darkMode={darkMode} />;
    }
  };

  return (
    <div className={darkMode ? 'dark' : ''}>
      <Toaster position="top-right" toastOptions={{ duration: 3000 }} />

      <div className={`min-h-screen flex flex-col ${darkMode ? 'bg-gray-950 text-white' : 'bg-slate-50 text-gray-900'}`}>
        <Navbar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          darkMode={darkMode}
          setDarkMode={setDarkMode}
          onLocateMe={handleLocateMe}
          locating={locating}
          userLocation={userLocation}
        />

        {locationError && (
          <div className="fixed top-14 left-0 right-0 z-40 bg-red-50 border-b border-red-200 text-red-700 text-xs px-4 py-2 flex items-center gap-2">
            <span>⚠️</span> {locationError}
          </div>
        )}

        {/* Main layout — fills viewport below navbar */}
        <div className={`flex flex-1 pt-14 ${locationError ? 'pt-20' : 'pt-14'}`} style={{ height: '100vh' }}>
          {/* Sidebar panel */}
          <aside className={`w-80 flex-shrink-0 flex flex-col overflow-y-auto border-r
            ${darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-slate-200'}`}>
            <div className="p-4 flex-1">
              {renderPanel()}
            </div>
          </aside>

          {/* Map fills remaining space */}
          <main className="flex-1 relative">
            <MapView
              routeCoords={routeCoords}
              routes={routes}
              gpsPoints={gpsPoints}
              darkMode={darkMode}
              trafficData={trafficData}
              anomalies={anomalies}
              liveAssets={liveAssets}
              measurePoints={measurePoints}
              userLocation={userLocation}
            />
          </main>
        </div>
      </div>
    </div>
  );
}

export default App;
