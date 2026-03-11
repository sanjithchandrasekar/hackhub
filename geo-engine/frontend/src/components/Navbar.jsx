import React from 'react';

const NAV_ITEMS = [
  { id: 'route',     icon: '🗺️',  label: 'Route'      },
  { id: 'geofence',  icon: '📍',  label: 'Geofence'   },
  { id: 'geocode',   icon: '🔍',  label: 'Search'     },
  { id: 'traffic',   icon: '🚦',  label: 'Traffic'    },
  { id: 'anomalies', icon: '⚠️',  label: 'Anomalies'  },
  { id: 'analytics', icon: '📊',  label: 'Analytics'  },
];

export default function Navbar({ activeTab, setActiveTab, darkMode, setDarkMode, onLocateMe, locating, userLocation }) {
  return (
    <header className={`fixed top-0 left-0 right-0 z-50 h-14 flex items-center justify-between px-4 shadow-md
      ${darkMode ? 'bg-gray-900 border-gray-700 text-white' : 'bg-white border-slate-200 text-gray-900'} border-b`}>

      {/* Brand */}
      <div className="flex items-center gap-2 min-w-[140px]">
        <span className="text-xl">🌍</span>
        <div>
          <span className="font-bold text-base tracking-tight">GeoEngine</span>
          <span className={`ml-2 text-[10px] font-medium px-1.5 py-0.5 rounded-full
            ${darkMode ? 'bg-blue-800 text-blue-200' : 'bg-blue-100 text-blue-700'}`}>
            Tamil Nadu
          </span>
        </div>
      </div>

      {/* Nav tabs */}
      <nav className="flex items-center gap-1">
        {NAV_ITEMS.map(({ id, icon, label }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
              ${activeTab === id
                ? 'bg-blue-600 text-white shadow-sm'
                : darkMode
                  ? 'text-gray-300 hover:bg-gray-800'
                  : 'text-gray-600 hover:bg-slate-100'
              }`}
          >
            <span>{icon}</span>
            <span className="hidden sm:inline">{label}</span>
          </button>
        ))}
      </nav>

      {/* Actions */}
      <div className="flex items-center gap-2 min-w-[140px] justify-end">
        <button
          onClick={onLocateMe}
          disabled={locating}
          title="Show my current location"
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
            ${userLocation
              ? 'bg-emerald-500 hover:bg-emerald-600 text-white'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
            } disabled:opacity-60 disabled:cursor-wait`}
        >
          {locating ? '⏳' : userLocation ? '📍' : '📍'}
          <span className="hidden sm:inline">{locating ? 'Locating…' : userLocation ? 'Located' : 'Locate Me'}</span>
        </button>

        <button
          onClick={() => setDarkMode(!darkMode)}
          title={darkMode ? 'Light mode' : 'Dark mode'}
          className={`w-8 h-8 rounded-lg flex items-center justify-center text-base transition-colors
            ${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-slate-100 hover:bg-slate-200'}`}
        >
          {darkMode ? '☀️' : '🌙'}
        </button>
      </div>
    </header>
  );
}
