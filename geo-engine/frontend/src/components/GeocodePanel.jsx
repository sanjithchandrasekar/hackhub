import React, { useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const TN_PLACES = [
  'Marina Beach, Chennai',
  'Meenakshi Temple, Madurai',
  'Brihadeeswarar Temple, Thanjavur',
  'Ooty, Nilgiris',
];

const TABS = [
  { id: 'forward', icon: '📍', label: 'Address → GPS' },
  { id: 'reverse', icon: '🔄', label: 'GPS → Address' },
  { id: 'poi',     icon: '🎯', label: 'Nearby POIs' },
];

export default function GeocodePanel({ darkMode }) {
  const [tab,       setTab]       = useState('forward');
  const [address,   setAddress]   = useState('Marina Beach, Chennai');
  const [lat,       setLat]       = useState('13.0827');
  const [lon,       setLon]       = useState('80.2707');
  const [radius,    setRadius]    = useState('2');
  const [category,  setCategory]  = useState('all');
  const [fResult,   setFResult]   = useState(null);
  const [rResult,   setRResult]   = useState(null);
  const [pois,      setPois]      = useState([]);
  const [loading,   setLoading]   = useState(false);

  const inp = `w-full px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500
    ${darkMode ? 'bg-gray-800 border-gray-600 text-white placeholder-gray-500' : 'bg-white border-slate-300 text-gray-900'}`;
  const lbl = `block text-xs font-semibold mb-1 uppercase tracking-wide ${darkMode ? 'text-gray-400' : 'text-gray-500'}`;
  const numInp = `${inp} font-mono`;

  const run = async (fn) => { setLoading(true); try { await fn(); } catch { toast.error('Request failed'); } finally { setLoading(false); } };

  const forward = () => run(async () => {
    const r = await axios.post('/geocode', { address });
    if (r.data.success) { setFResult(r.data); toast.success('Location found!'); }
    else toast.error('Address not found');
  });

  const reverse = () => run(async () => {
    const r = await axios.post('/reverse-geocode', { lat: parseFloat(lat), lon: parseFloat(lon) });
    if (r.data.success) { setRResult(r.data); toast.success('Address found!'); }
    else toast.error('No address at those coordinates');
  });

  const searchPoi = () => run(async () => {
    const r = await axios.post('/poi/search', { lat: parseFloat(lat), lon: parseFloat(lon), radius_km: parseFloat(radius), category });
    setPois(r.data.pois || []);
    toast.success(`${(r.data.pois || []).length} POIs found`);
  });

  const statBox = (val, lbl) => (
    <div className={`rounded-lg p-3 text-center ${darkMode ? 'bg-gray-700' : 'bg-slate-50'}`}>
      <div className={`text-sm font-bold ${darkMode ? 'text-white' : 'text-gray-800'}`}>{val}</div>
      <div className={`text-[10px] ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{lbl}</div>
    </div>
  );

  return (
    <div>
      <h2 className={`text-base font-bold mb-4 ${darkMode ? 'text-white' : 'text-gray-800'}`}>🔍 Location Search</h2>

      {/* Tab bar */}
      <div className={`flex rounded-xl p-1 mb-4 ${darkMode ? 'bg-gray-800' : 'bg-slate-100'}`}>
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-colors
              ${tab === t.id
                ? 'bg-blue-600 text-white shadow-sm'
                : (darkMode ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-700')}`}
          >
            {t.icon} <span className="ml-1 hidden sm:inline">{t.label.split(' ')[0]}</span>
          </button>
        ))}
      </div>

      {/* Forward */}
      {tab === 'forward' && (
        <>
          <div className="mb-3">
            <label className={lbl}>Enter Address</label>
            <input value={address} onChange={e => setAddress(e.target.value)} placeholder="Address…" className={inp} />
          </div>
          <div className="flex flex-wrap gap-1 mb-3">
            {TN_PLACES.map(p => (
              <button key={p} onClick={() => setAddress(p)}
                className={`text-[10px] px-2 py-0.5 rounded-full font-medium
                  ${darkMode ? 'bg-gray-700 text-blue-300 hover:bg-blue-900' : 'bg-blue-50 text-blue-700 hover:bg-blue-100'}`}>
                {p.split(',')[0]}
              </button>
            ))}
          </div>
          <button onClick={forward} disabled={loading}
            className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm transition-colors disabled:opacity-60 mb-3">
            {loading ? '⏳ Searching…' : '🔍 Get Coordinates'}
          </button>
          {fResult?.success && (
            <div className={`rounded-xl border p-4 ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-emerald-50 border-emerald-200'}`}>
              <div className={`text-xs font-semibold mb-2 ${darkMode ? 'text-emerald-400' : 'text-emerald-700'}`}>📍 Location Found!</div>
              <div className="grid grid-cols-2 gap-2">
                {statBox(fResult.latitude?.toFixed(5), 'Latitude')}
                {statBox(fResult.longitude?.toFixed(5), 'Longitude')}
              </div>
              {fResult.display_name && <p className={`text-xs mt-2 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{fResult.display_name}</p>}
            </div>
          )}
        </>
      )}

      {/* Reverse */}
      {tab === 'reverse' && (
        <>
          <div className="mb-3">
            <label className={lbl}>GPS Coordinates</label>
            <div className="flex gap-2">
              <input type="number" step="0.0001" value={lat} onChange={e => setLat(e.target.value)} placeholder="Lat" className={numInp} />
              <input type="number" step="0.0001" value={lon} onChange={e => setLon(e.target.value)} placeholder="Lon" className={numInp} />
            </div>
          </div>
          <button onClick={reverse} disabled={loading}
            className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm transition-colors disabled:opacity-60 mb-3">
            {loading ? '⏳ Searching…' : '🔍 Get Address'}
          </button>
          {rResult?.success && (
            <div className={`rounded-xl border p-4 ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-emerald-50 border-emerald-200'}`}>
              <div className={`text-xs font-semibold mb-1 ${darkMode ? 'text-emerald-400' : 'text-emerald-700'}`}>📮 Address Found!</div>
              <p className={`text-sm ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>{rResult.display_name}</p>
              {rResult.address && (
                <div className={`text-xs mt-2 space-y-0.5 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  {rResult.address.city     && <div>🏙️ {rResult.address.city}</div>}
                  {rResult.address.road     && <div>🛣️ {rResult.address.road}</div>}
                  {rResult.address.postcode && <div>📬 {rResult.address.postcode}</div>}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* POI */}
      {tab === 'poi' && (
        <>
          <div className="mb-3">
            <label className={lbl}>Search Centre (Lat / Lon)</label>
            <div className="flex gap-2">
              <input type="number" step="0.0001" value={lat} onChange={e => setLat(e.target.value)} placeholder="Lat" className={numInp} />
              <input type="number" step="0.0001" value={lon} onChange={e => setLon(e.target.value)} placeholder="Lon" className={numInp} />
            </div>
          </div>
          <div className="mb-3">
            <label className={lbl}>Radius (km)</label>
            <input type="number" step="0.5" value={radius} onChange={e => setRadius(e.target.value)} className={inp} />
          </div>
          <div className="mb-3">
            <label className={lbl}>Category</label>
            <select value={category} onChange={e => setCategory(e.target.value)} className={inp}>
              <option value="all">All Categories</option>
              <option value="restaurant">🍽️ Restaurants</option>
              <option value="shopping">🛍️ Shopping</option>
              <option value="park">🌳 Parks</option>
              <option value="religious">🕌 Religious</option>
              <option value="tourist">🏛️ Tourist Spots</option>
            </select>
          </div>
          <button onClick={searchPoi} disabled={loading}
            className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm transition-colors disabled:opacity-60 mb-3">
            {loading ? '⏳ Searching…' : '🎯 Search POIs'}
          </button>
          {pois.length > 0 && (
            <div>
              <div className={`text-xs font-semibold uppercase tracking-wide mb-2 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                {pois.length} places found
              </div>
              {pois.map((p, i) => (
                <div key={i} className={`rounded-xl border px-4 py-2.5 mb-2 ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-slate-200 shadow-sm'}`}>
                  <div className="flex justify-between items-start">
                    <span className={`text-sm font-semibold ${darkMode ? 'text-white' : 'text-gray-800'}`}>{p.name}</span>
                    <span className={`text-xs px-1.5 py-0.5 rounded-full ${darkMode ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-700'}`}>{p.distance_km} km</span>
                  </div>
                  <div className={`text-xs mt-0.5 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                    {p.lat?.toFixed(4)}, {p.lon?.toFixed(4)} · {p.type}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}


