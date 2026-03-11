import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend,
} from "recharts";

const TABS = [
  { id: "routes",   label: "Routes" },
  { id: "ml",       label: "ML Stats" },
  { id: "geofence", label: "Geofence" },
];

const PIE_COLORS = ["#4CAF50", "#FF9800", "#F44336", "#2196F3", "#9C27B0"];

export default function AnalyticsPanel({ darkMode }) {
  const [tab,     setTab]     = useState("routes");
  const [routes,  setRoutes]  = useState(null);
  const [ml,      setMl]      = useState(null);
  const [geo,     setGeo]     = useState(null);
  const [loading, setLoading] = useState(false);

  const clr = darkMode ? "#374151" : "#e5e7eb";
  const txt = darkMode ? "#9ca3af" : "#6b7280";
  const card = `rounded-xl border p-3 mb-3 ${darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-slate-200 shadow-sm"}`;

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [r1, r2, r3] = await Promise.allSettled([
        axios.get("/analytics/routes"),
        axios.get("/analytics/ml"),
        axios.get("/analytics/geofence"),
      ]);
      if (r1.status === "fulfilled") setRoutes(r1.value.data);
      if (r2.status === "fulfilled") setMl(r2.value.data);
      if (r3.status === "fulfilled") setGeo(r3.value.data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const chartData = (routes?.recent_routes || []).slice(-10).map((r, i) => ({
    name: "R" + (i + 1),
    distance: Number(r.distance_km) || 0,
    eta: Math.round(r.eta_min || r.estimated_time_min) || 0,
  }));

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className={`text-base font-bold ${darkMode ? "text-white" : "text-gray-800"}`}>Analytics</h2>
        <button onClick={fetchAll} disabled={loading}
          className={`text-xs px-3 py-1.5 rounded-lg font-semibold transition-colors disabled:opacity-60
            ${darkMode ? "bg-gray-700 hover:bg-gray-600 text-white" : "bg-slate-100 hover:bg-slate-200 text-gray-700"}`}>
          {loading ? "..." : "Refresh"}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-colors
              ${tab === t.id ? "bg-blue-600 text-white" : darkMode ? "bg-gray-700 text-gray-300" : "bg-slate-100 text-gray-600"}`}>
            {t.label}
          </button>
        ))}
      </div>

      {/*  ROUTES TAB  */}
      {tab === "routes" && (
        <>
          {routes && (
            <div className="grid grid-cols-2 gap-2 mb-4">
              {[
                { val: routes.total_routes,                 lbl: "Total Routes" },
                { val: routes.avg_distance_km,              lbl: "Avg Dist km"  },
                { val: Math.round(routes.avg_time_min),     lbl: "Avg ETA min"  },
                { val: (routes.recent_routes || []).length, lbl: "Recent"       },
              ].map(({ val, lbl }) => (
                <div key={lbl} className={`rounded-xl p-3 text-center border
                  ${darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-slate-200 shadow-sm"}`}>
                  <div className={`text-xl font-bold ${darkMode ? "text-white" : "text-gray-800"}`}>{val ?? "-"}</div>
                  <div className={`text-[10px] ${darkMode ? "text-gray-500" : "text-gray-400"}`}>{lbl}</div>
                </div>
              ))}
            </div>
          )}

          {chartData.length > 0 && (
            <>
              <div className={card}>
                <div className={`text-xs font-semibold uppercase tracking-wide mb-2 ${darkMode ? "text-gray-400" : "text-gray-500"}`}>Distance per Route (km)</div>
                <ResponsiveContainer width="100%" height={130}>
                  <BarChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={clr} />
                    <XAxis dataKey="name" tick={{ fill: txt, fontSize: 10 }} />
                    <YAxis tick={{ fill: txt, fontSize: 10 }} />
                    <Tooltip contentStyle={{ background: darkMode ? "#1f2937" : "#fff", border: "none", borderRadius: 8, fontSize: 12 }} />
                    <Bar dataKey="distance" fill="#2563eb" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className={card}>
                <div className={`text-xs font-semibold uppercase tracking-wide mb-2 ${darkMode ? "text-gray-400" : "text-gray-500"}`}>ETA per Route (min)</div>
                <ResponsiveContainer width="100%" height={120}>
                  <LineChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={clr} />
                    <XAxis dataKey="name" tick={{ fill: txt, fontSize: 10 }} />
                    <YAxis tick={{ fill: txt, fontSize: 10 }} />
                    <Tooltip contentStyle={{ background: darkMode ? "#1f2937" : "#fff", border: "none", borderRadius: 8, fontSize: 12 }} />
                    <Line type="monotone" dataKey="eta" stroke="#10b981" strokeWidth={2} dot={{ r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </>
          )}

          {!routes && !loading && (
            <div className={`rounded-xl border p-6 text-center ${darkMode ? "bg-gray-800 border-gray-700 text-gray-400" : "bg-slate-50 border-slate-200 text-gray-400"}`}>
              <div className="text-3xl mb-2"></div>
              <div className="text-sm">No analytics data yet.</div>
            </div>
          )}
        </>
      )}

      {/*  ML TAB  */}
      {tab === "ml" && (
        <>
          {ml && (
            <>
              <div className="grid grid-cols-2 gap-2 mb-4">
                {[
                  { val: ml.total_predictions,    lbl: "Predictions" },
                  { val: ml.ml_model_count,        lbl: "ML Model"    },
                  { val: ml.heuristic_count,       lbl: "Heuristic"   },
                  { val: ml.anomalies_detected,    lbl: "Anomalies"   },
                ].map(({ val, lbl }) => (
                  <div key={lbl} className={`rounded-xl p-3 text-center border
                    ${darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-slate-200 shadow-sm"}`}>
                    <div className={`text-xl font-bold ${darkMode ? "text-white" : "text-gray-800"}`}>{val ?? "-"}</div>
                    <div className={`text-[10px] ${darkMode ? "text-gray-500" : "text-gray-400"}`}>{lbl}</div>
                  </div>
                ))}
              </div>

              {ml.models_trained && (
                <div className={card}>
                  <div className={`text-xs font-semibold uppercase tracking-wide mb-2 ${darkMode ? "text-gray-400" : "text-gray-500"}`}>Model Status</div>
                  {Object.entries(ml.models_trained).map(([m, trained]) => (
                    <div key={m} className={`flex items-center justify-between py-1.5 text-xs border-b last:border-0
                      ${darkMode ? "border-gray-700 text-gray-300" : "border-slate-100 text-gray-700"}`}>
                      <span className="capitalize">{m.replace("_", " ")}</span>
                      <span className={trained ? "text-emerald-500 font-semibold" : "text-red-400"}>{trained ? "Trained" : "Not trained"}</span>
                    </div>
                  ))}
                </div>
              )}

              {ml.congestion_distribution && Object.keys(ml.congestion_distribution).length > 0 && (
                <div className={card}>
                  <div className={`text-xs font-semibold uppercase tracking-wide mb-2 ${darkMode ? "text-gray-400" : "text-gray-500"}`}>Congestion Distribution</div>
                  <ResponsiveContainer width="100%" height={160}>
                    <PieChart>
                      <Pie data={Object.entries(ml.congestion_distribution).map(([name, value]) => ({ name, value }))}
                        cx="50%" cy="50%" outerRadius={60} dataKey="value" label={({ name, percent }) => `${name} ${Math.round(percent * 100)}%`}
                        labelLine={false}>
                        {Object.keys(ml.congestion_distribution).map((_, i) => (
                          <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}
            </>
          )}
          {!ml && !loading && (
            <div className={`rounded-xl border p-6 text-center ${darkMode ? "bg-gray-800 border-gray-700 text-gray-400" : "bg-slate-50 border-slate-200 text-gray-400"}`}>
              <div className="text-3xl mb-2"></div>
              <div className="text-sm">No ML data yet. Try sending telemetry!</div>
            </div>
          )}
        </>
      )}

      {/*  GEOFENCE TAB  */}
      {tab === "geofence" && (
        <>
          {geo && (
            <>
              <div className="grid grid-cols-2 gap-2 mb-4">
                {[
                  { val: geo.total_events,  lbl: "Total Events" },
                  { val: geo.entry_events,  lbl: "Entries"      },
                  { val: geo.exit_events,   lbl: "Exits"        },
                  { val: geo.unique_assets, lbl: "Assets"       },
                ].map(({ val, lbl }) => (
                  <div key={lbl} className={`rounded-xl p-3 text-center border
                    ${darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-slate-200 shadow-sm"}`}>
                    <div className={`text-xl font-bold ${darkMode ? "text-white" : "text-gray-800"}`}>{val ?? "-"}</div>
                    <div className={`text-[10px] ${darkMode ? "text-gray-500" : "text-gray-400"}`}>{lbl}</div>
                  </div>
                ))}
              </div>

              {(geo.recent_events || []).length > 0 && (
                <div>
                  <div className={`text-xs font-semibold uppercase tracking-wide mb-2 ${darkMode ? "text-gray-400" : "text-gray-500"}`}>Recent Events</div>
                  {geo.recent_events.slice(0, 6).map((ev, i) => (
                    <div key={i} className={`rounded-xl border px-4 py-2.5 mb-2
                      ${darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-slate-200 shadow-sm"}`}>
                      <div className="flex items-center justify-between">
                        <span className={`text-sm font-semibold ${darkMode ? "text-white" : "text-gray-800"}`}>
                          {ev.asset_id}
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-semibold
                          ${ev.event === "ENTRY" ? "bg-emerald-100 text-emerald-700" : "bg-orange-100 text-orange-700"}`}>
                          {ev.event}
                        </span>
                      </div>
                      <div className={`text-xs mt-0.5 ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
                        {ev.campus || "Unknown campus"}
                        {ev.timestamp && <span className="ml-2 opacity-60">{new Date(ev.timestamp).toLocaleTimeString()}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
          {!geo && !loading && (
            <div className={`rounded-xl border p-6 text-center ${darkMode ? "bg-gray-800 border-gray-700 text-gray-400" : "bg-slate-50 border-slate-200 text-gray-400"}`}>
              <div className="text-3xl mb-2"></div>
              <div className="text-sm">No geofence data yet.</div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
