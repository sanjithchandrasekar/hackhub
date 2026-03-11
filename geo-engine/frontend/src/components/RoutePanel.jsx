import React, { useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const TN_LOCS = [
  { name: 'Chennai',    lat: 13.0827, lon: 80.2707 },
  { name: 'Coimbatore', lat: 11.0168, lon: 76.9558 },
  { name: 'Madurai',    lat: 9.9252,  lon: 78.1198 },
  { name: 'Salem',      lat: 11.6643, lon: 78.1460 },
  { name: 'Trichy',     lat: 10.7905, lon: 78.7047 },
  { name: 'Vellore',    lat: 12.9165, lon: 79.1325 },
];

const CONGESTION_COLOR = {
  'Free Flow': 'text-emerald-500', 'Low Traffic': 'text-green-500',
  'Moderate': 'text-yellow-500', 'High Congestion': 'text-orange-500', 'Severe': 'text-red-600',
};

function LocChip({ label, onClick, dark }) {
  return (
    <button type="button" onClick={onClick}
      className={`text-[10px] px-2 py-0.5 rounded-full font-medium transition-colors
        ${dark ? 'bg-gray-700 text-blue-300 hover:bg-blue-900' : 'bg-blue-50 text-blue-700 hover:bg-blue-100'}`}>
      {label}
    </button>
  );
}

function Field({ label, value, onChange, dark }) {
  return (
    <input type="number" step="0.0001" value={value} onChange={e => onChange(e.target.value)}
      placeholder={label}
      className={`w-full px-3 py-2 rounded-lg border text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500
        ${dark ? 'bg-gray-800 border-gray-600 text-white placeholder-gray-500' : 'bg-white border-slate-300 text-gray-900'}`} />
  );
}

function SafetyBadge({ score }) {
  if (score == null) return null;
  const color = score >= 7 ? 'bg-emerald-100 text-emerald-700' : score >= 4 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700';
  const lbl   = score >= 7 ? 'Safe' : score >= 4 ? 'Moderate' : 'Risky';
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold ${color}`}>
      {String.fromCodePoint(0x1F6E1)} {lbl} ({score}/10)
    </span>
  );
}

function LocationSearch({ placeholder, query, setQuery, onSelect, dark }) {
  const [results, setResults] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    if (!query || query.trim().length === 0) {
      setResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await axios.get(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&countrycodes=in`);
        setResults(res.data || []);
      } catch (err) {
        // ignore
      } finally {
        setLoading(false);
      }
    }, 600);
    return () => clearTimeout(timer);
  }, [query]);

  return (
    <div className="relative mb-2 w-full">
      <div className="relative">
        <input 
          type="text"
          placeholder={loading ? "Searching..." : placeholder}
          value={query}
          onChange={e => { setQuery(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 200)}
          className={`w-full px-3 py-2 text-sm rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500 pr-8
            ${dark ? 'bg-gray-800 border-gray-600 text-white placeholder-gray-500' : 'bg-white border-slate-300 text-gray-900'}`}
        />
        {query && (
          <button type="button" onClick={() => { setQuery(''); setResults([]); }}
            className={`absolute right-2 top-2 text-lg leading-none ${dark ? 'text-gray-400' : 'text-gray-500'}`}>
            &times;
          </button>
        )}
      </div>
      {open && results.length > 0 && (
        <div className={`absolute z-50 w-full mt-1 max-h-48 overflow-y-auto rounded-lg shadow-lg border text-xs
          ${dark ? 'bg-gray-800 border-gray-600 text-white' : 'bg-white border-slate-200'}`}>
          {results.map((r, i) => (
            <div key={i} className={`px-3 py-2 cursor-pointer border-b last:border-0 ${dark ? 'border-gray-700 hover:bg-gray-700' : 'border-slate-100 hover:bg-slate-100'}`}
                 onMouseDown={(e) => {
                   e.preventDefault();
                   const name = r.display_name.split(',')[0];
                   setQuery(name); 
                   setOpen(false);
                   onSelect({ lat: r.lat, lon: r.lon }, name);
                 }}>
              <div className="font-semibold truncate">{r.display_name.split(',')[0]}</div>
              <div className={`text-[10px] truncate ${dark ? 'text-gray-400' : 'text-gray-500'}`}>{r.display_name}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


export default function RoutePanel({ onRouteCalculated, onRoutesCalculated, darkMode }) {
  const [startQuery, setStartQuery] = useState('');
  const [endQuery,   setEndQuery]   = useState('');
  const [startLat, setStartLat] = useState('13.0827');
  const [startLon, setStartLon] = useState('80.2707');
  const [endLat,   setEndLat]   = useState('11.0168');
  const [endLon,   setEndLon]   = useState('76.9558');
  const [mode,     setMode]     = useState('fastest');
  const [multiMode, setMultiMode] = useState(false);
  const [loading,  setLoading]  = useState(false);
  const [result,   setResult]   = useState(null);
  const [routes,   setRoutes]   = useState([]);
  const [selIdx,   setSelIdx]   = useState(0);

  const card  = `rounded-xl border p-4 mb-3 ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-slate-200 shadow-sm'}`;
  const label = `block text-xs font-semibold mb-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'} uppercase tracking-wide`;
  const sel   = `w-full px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500
    ${darkMode ? 'bg-gray-800 border-gray-600 text-white' : 'bg-white border-slate-300 text-gray-900'}`;

  const setLoc = (loc, isStart, name) => {
    if (isStart) { 
      setStartLat(String(loc.lat)); 
      setStartLon(String(loc.lon)); 
      if (name) setStartQuery(name);
    }
    else { 
      setEndLat(String(loc.lat));   
      setEndLon(String(loc.lon)); 
      if (name) setEndQuery(name);
    }
  };

  const reverseRoute = () => {
    const tempLat = startLat;
    const tempLon = startLon;
    const tempQ   = startQuery;
    setStartLat(endLat);
    setStartLon(endLon);
    setStartQuery(endQuery);
    setEndLat(tempLat);
    setEndLon(tempLon);
    setEndQuery(tempQ);
  };

  const handleCalculate = async () => {
    setLoading(true);
    setResult(null);
    setRoutes([]);
    try {
      if (multiMode) {
        const res = await axios.post('/multi-route', {
          start_lat: parseFloat(startLat), start_lon: parseFloat(startLon),
          end_lat:   parseFloat(endLat),   end_lon:   parseFloat(endLon),
        });
        const alts = res.data.routes || [];
        setRoutes(alts);
        setSelIdx(0);
        if (onRoutesCalculated) onRoutesCalculated(alts);
        if (alts[0]?.route && onRouteCalculated) onRouteCalculated(alts[0].route);
        toast.success(`${alts.length} routes found`);
      } else {
        const res = await axios.post('/route', {
          start_lat: parseFloat(startLat), start_lon: parseFloat(startLon),
          end_lat:   parseFloat(endLat),   end_lon:   parseFloat(endLon), mode,
        });
        setResult(res.data);
        if (onRoutesCalculated) onRoutesCalculated(null);
        if (res.data.route && onRouteCalculated) onRouteCalculated(res.data.route);
        toast.success('Route calculated!');
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Route calculation failed');
    } finally {
      setLoading(false);
    }
  };

  const pickRoute = (r, i) => {
    setSelIdx(i);
    if (r.route && onRouteCalculated) onRouteCalculated(r.route);
  };

  return (
    <div>
      <h2 className={`text-base font-bold mb-4 flex items-center gap-2 ${darkMode ? 'text-white' : 'text-gray-800'}`}>
        Route Planner
      </h2>

      <div className="flex gap-2 mb-4">
        <button onClick={() => setMultiMode(false)}
          className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-colors
            ${!multiMode ? 'bg-blue-600 text-white' : darkMode ? 'bg-gray-700 text-gray-300' : 'bg-slate-100 text-gray-600'}`}>
          Single Route
        </button>
        <button onClick={() => setMultiMode(true)}
          className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-colors
            ${multiMode ? 'bg-blue-600 text-white' : darkMode ? 'bg-gray-700 text-gray-300' : 'bg-slate-100 text-gray-600'}`}>
          Multi-Route
        </button>
      </div>

      {!multiMode && (
        <div className="mb-4">
          <label className={label}>Route Mode</label>
          <select value={mode} onChange={e => setMode(e.target.value)} className={sel}>
            <option value="fastest">Fastest</option>
            <option value="shortest">Shortest</option>
            <option value="balanced">Balanced</option>
          </select>
        </div>
      )}

      <div className="mb-4">
        <div className="flex justify-between items-center mb-1">
          <label className={label}>Start Location</label>
        </div>
        <LocationSearch placeholder="Search start location..." query={startQuery} setQuery={setStartQuery} onSelect={(loc, name) => setLoc(loc, true, name)} dark={darkMode} />
        <div className="flex gap-2 mb-1">
          <Field label="Lat" value={startLat} onChange={setStartLat} dark={darkMode} />
          <Field label="Lon" value={startLon} onChange={setStartLon} dark={darkMode} />
        </div>
        <div className="flex flex-wrap gap-1 mt-1">
          {TN_LOCS.map(loc => (
            <LocChip key={loc.name} label={loc.name} onClick={() => setLoc(loc, true, loc.name)} dark={darkMode} />
          ))}
        </div>
      </div>

      <div className="flex justify-center -my-3 relative z-10">
        <button onClick={reverseRoute} type="button"
          className={`p-1.5 rounded-full border shadow-sm transition-transform hover:scale-110
            ${darkMode ? 'bg-gray-700 border-gray-600 text-gray-300' : 'bg-white border-slate-200 text-gray-600'}`}>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
          </svg>
        </button>
      </div>

      <div className="mb-4">
        <label className={label}>End Location</label>
        <LocationSearch placeholder="Search destination..." query={endQuery} setQuery={setEndQuery} onSelect={(loc, name) => setLoc(loc, false, name)} dark={darkMode} />
        <div className="flex gap-2 mb-1">
          <Field label="Lat" value={endLat} onChange={setEndLat} dark={darkMode} />
          <Field label="Lon" value={endLon} onChange={setEndLon} dark={darkMode} />
        </div>
        <div className="flex flex-wrap gap-1 mt-1">
          {TN_LOCS.map(loc => (
            <LocChip key={loc.name} label={loc.name} onClick={() => setLoc(loc, false, loc.name)} dark={darkMode} />
          ))}
        </div>
      </div>

      <button onClick={handleCalculate} disabled={loading}
        className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm
          transition-colors disabled:opacity-60 flex items-center justify-center gap-2 mb-4">
        {loading ? <span className="animate-spin">...</span> : null}
        {multiMode ? 'Find Best Routes' : 'Calculate Route'}
      </button>

      {result && !multiMode && (
        <div className={card}>
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-emerald-500">Route Ready</span>
            <SafetyBadge score={result.safety_score} />
          </div>
          <div className="grid grid-cols-2 gap-2 mb-3">
            {[
              { val: `${(result.distance_km || 0).toFixed(1)} km`, lbl: 'Distance' },
              { val: `${Math.round(result.eta_min || result.estimated_time_min || 0)} min`, lbl: 'ETA' },
              { val: result.waypoints_count, lbl: 'Waypoints' },
              { val: result.mode || mode, lbl: 'Mode' },
            ].map(({ val, lbl }) => (
              <div key={lbl} className={`rounded-lg p-3 text-center ${darkMode ? 'bg-gray-700' : 'bg-slate-50'}`}>
                <div className={`text-base font-bold ${darkMode ? 'text-white' : 'text-gray-800'}`}>{val}</div>
                <div className={`text-[10px] ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{lbl}</div>
              </div>
            ))}
          </div>
          {result.congestion && (
            <div className={`flex items-center gap-2 text-xs px-3 py-2 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-slate-50'}`}>
              <span>Congestion:</span>
              <span className={`font-semibold ${CONGESTION_COLOR[result.congestion.label] || ''}`}>
                {result.congestion.label}
              </span>
              <span className="ml-auto opacity-60">{Math.round((result.congestion.congestion_score || 0) * 100)}%</span>
            </div>
          )}
        </div>
      )}

      {routes.length > 0 && multiMode && (
        <div>
          <div className={`text-xs font-semibold mb-2 uppercase tracking-wide ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            {routes.length} Alternatives
          </div>
          {routes.map((r, i) => {
            const bdr = (r.safety_score >= 7) ? 'border-emerald-400' : (r.safety_score >= 4) ? 'border-yellow-400' : 'border-red-400';
            return (
              <button key={i} type="button" onClick={() => pickRoute(r, i)}
                className={`w-full text-left rounded-xl border-2 px-4 py-3 mb-2 transition-all
                  ${selIdx === i ? bdr : darkMode ? 'border-gray-700' : 'border-slate-200'}
                  ${darkMode ? 'bg-gray-800 hover:border-blue-500' : 'bg-white hover:border-blue-400 shadow-sm'}`}>
                <div className="flex justify-between items-center mb-1">
                  <span className={`font-semibold text-sm ${darkMode ? 'text-white' : 'text-gray-800'}`}>
                    {r.label || `Route ${i + 1}`}
                  </span>
                  <SafetyBadge score={r.safety_score} />
                </div>
                <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'} flex gap-3 flex-wrap`}>
                  <span>{(r.distance_km || 0).toFixed(1)} km</span>
                  <span>{Math.round(r.eta_min || r.duration_min || 0)} min</span>
                  {r.congestion?.label && (
                    <span className={CONGESTION_COLOR[r.congestion.label] || ''}>{r.congestion.label}</span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
  
