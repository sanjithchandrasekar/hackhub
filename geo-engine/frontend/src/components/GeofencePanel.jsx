import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const QUICK_LOCS = [
  { name: 'Chennai',    lat: 13.0827, lon: 80.2707 },
  { name: 'Coimbatore', lat: 11.0168, lon: 76.9558 },
  { name: 'Madurai',    lat: 9.9252,  lon: 78.1198 },
  { name: 'Trichy',     lat: 10.7905, lon: 78.7047 },
];

export default function GeofencePanel({ onLocationChecked, darkMode, userLocation }) {
  const [lat, setLat] = useState('13.0827');
  const [lon, setLon] = useState('80.2707');
  const [loading,  setLoading]  = useState(false);
  const [result,   setResult]   = useState(null);
  const [campuses, setCampuses] = useState([]);

  const inp = `w-full px-3 py-2 rounded-lg border text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500
    ${darkMode ? 'bg-gray-800 border-gray-600 text-white placeholder-gray-500' : 'bg-white border-slate-300 text-gray-900'}`;
  const lbl = `block text-xs font-semibold mb-1 uppercase tracking-wide ${darkMode ? 'text-gray-400' : 'text-gray-500'}`;

  useEffect(() => {
    axios.get('/geofence')
      .then(r => setCampuses(r.data.campuses || []))
      .catch(() => {});
  }, []);

  const handleCheck = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await axios.post('/geofence', { lat: parseFloat(lat), lon: parseFloat(lon) });
      setResult(res.data);
      if (onLocationChecked) onLocationChecked({ lat: parseFloat(lat), lon: parseFloat(lon), ...res.data });
    } catch {
      toast.error('Geofence check failed');
    } finally {
      setLoading(false);
    }
  };

  const useCurrentLocation = () => {
    if (!navigator.geolocation) return toast.error('Geolocation not supported');
    navigator.geolocation.getCurrentPosition(
      pos => { setLat(pos.coords.latitude.toFixed(6)); setLon(pos.coords.longitude.toFixed(6)); toast.success('Location set!'); },
      ()  => toast.error('Failed to get location'),
    );
  };

  return (
    <div>
      <h2 className={`text-base font-bold mb-4 flex items-center gap-2 ${darkMode ? 'text-white' : 'text-gray-800'}`}>
        📍 Geofence Checker
      </h2>

      {/* Inputs */}
      <div className="mb-3">
        <label className={lbl}>Test Coordinates</label>
        <div className="flex gap-2">
          <input type="number" step="0.0001" value={lat} onChange={e => setLat(e.target.value)} placeholder="Latitude"  className={inp} />
          <input type="number" step="0.0001" value={lon} onChange={e => setLon(e.target.value)} placeholder="Longitude" className={inp} />
        </div>
      </div>

      {/* Quick locations */}
      <div className="flex flex-wrap gap-1 mb-4">
        {QUICK_LOCS.map(loc => (
          <button
            key={loc.name}
            type="button"
            onClick={() => { setLat(String(loc.lat)); setLon(String(loc.lon)); }}
            className={`text-[10px] px-2 py-0.5 rounded-full font-medium
              ${darkMode ? 'bg-gray-700 text-blue-300 hover:bg-blue-900' : 'bg-blue-50 text-blue-700 hover:bg-blue-100'}`}
          >
            {loc.name}
          </button>
        ))}
      </div>

      {/* Actions */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={handleCheck}
          disabled={loading}
          className="flex-1 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm transition-colors disabled:opacity-60"
        >
          {loading ? '⏳ Checking…' : '🔍 Check Geofence'}
        </button>
        <button
          onClick={useCurrentLocation}
          className={`flex-1 py-2.5 rounded-xl font-semibold text-sm transition-colors
            ${darkMode ? 'bg-gray-700 hover:bg-gray-600 text-white' : 'bg-slate-100 hover:bg-slate-200 text-gray-700'}`}
        >
          📍 My Location
        </button>
      </div>

      {/* Result */}
      {result && (
        <div className={`rounded-xl border p-4 mb-4 ${result.inside
          ? (darkMode ? 'bg-emerald-900/40 border-emerald-700' : 'bg-emerald-50 border-emerald-300')
          : (darkMode ? 'bg-amber-900/30 border-amber-700'    : 'bg-amber-50  border-amber-300')}`}
        >
          <div className={`font-bold text-sm mb-2 ${result.inside
            ? (darkMode ? 'text-emerald-300' : 'text-emerald-700')
            : (darkMode ? 'text-amber-300'   : 'text-amber-700')}`}
          >
            {result.inside ? '✅ Inside Geofence' : '⚠️ Outside Geofences'}
          </div>
          {result.inside && result.campus && (
            <div className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <div>📍 <strong>Campus:</strong> {result.campus}</div>
              {result.event && <div className="mt-1 text-xs">🎉 Event: {result.event}</div>}
            </div>
          )}
          {!result.inside && result.nearest_campus && (
            <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              <div>Nearest: {result.nearest_campus}</div>
              <div>Distance: {Number(result.distance_to_nearest_km).toFixed(2)} km</div>
            </div>
          )}
        </div>
      )}

      {/* Campus list */}
      {campuses.length > 0 && (
        <div>
          <div className={`text-xs font-semibold uppercase tracking-wide mb-2 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            {campuses.length} Geofences
          </div>
          {campuses.map((c, i) => (
            <div key={i} className={`rounded-xl border px-4 py-2.5 mb-2 flex items-center justify-between
              ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-slate-200 shadow-sm'}`}>
              <span className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-800'}`}>{c.name}</span>
              <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: (c.color || '#2563EB') + '22', color: c.color || '#2563EB' }}>
                {c.type}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


