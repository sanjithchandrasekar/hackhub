import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import toast from "react-hot-toast";

const CONGESTION_DOT = {
  "Free Flow":       "bg-emerald-400",
  "Low Traffic":     "bg-green-400",
  "Moderate":        "bg-yellow-400",
  "High Congestion": "bg-orange-500",
  "Severe":          "bg-red-600",
};

function HotspotRow({ hotspot, dark }) {
  const dot = CONGESTION_DOT[hotspot.congestion_label] || "bg-gray-400";
  return (
    <div className={`flex items-center justify-between px-3 py-2.5 rounded-xl border mb-2
      ${dark ? "bg-gray-800 border-gray-700" : "bg-white border-slate-200 shadow-sm"}`}>
      <div className="flex items-center gap-2.5">
        <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${dot}`} />
        <div>
          <div className={`text-sm font-semibold ${dark ? "text-white" : "text-gray-800"}`}>
            {hotspot.city || hotspot.name || "Unknown"}
          </div>
          <div className={`text-[10px] ${dark ? "text-gray-400" : "text-gray-500"}`}>
            {hotspot.lat != null ? hotspot.lat.toFixed(4) : "-"}, {hotspot.lon != null ? hotspot.lon.toFixed(4) : "-"}
          </div>
        </div>
      </div>
      <div className="text-right">
        <div className={`text-sm font-bold ${dark ? "text-white" : "text-gray-800"}`}>
          {hotspot.speed_kmh != null ? Math.round(hotspot.speed_kmh) + " km/h" : "-"}
        </div>
        <div className={`text-[10px] ${dark ? "text-gray-400" : "text-gray-500"}`}>
          {Math.round((hotspot.intensity || 0) * 100)}% intensity
        </div>
      </div>
    </div>
  );
}

export default function TrafficPanel({ darkMode, onHeatmapData }) {
  const [hotspots, setHotspots] = useState([]);
  const [loading,  setLoading]  = useState(false);
  const [lastRefresh, setLast]  = useState(null);
  const [prediction, setPred]   = useState(null);
  const [predHour, setPredHour] = useState(new Date().getHours());

  const lbl  = "block text-xs font-semibold mb-1 uppercase tracking-wide " + (darkMode ? "text-gray-400" : "text-gray-500");
  const card = "rounded-xl border p-4 mb-3 " + (darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-slate-200 shadow-sm");

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const r = await axios.get("/traffic-heatmap");
      const pts = r.data.hotspots || r.data.heatmap || [];
      setHotspots(pts);
      setLast(new Date());
      if (onHeatmapData) onHeatmapData(pts);
    } catch {
      toast.error("Failed to load traffic data");
    } finally {
      setLoading(false);
    }
  }, [onHeatmapData]);

  const predictCongestion = async () => {
    try {
      const r = await axios.get("/predict/congestion?hour=" + predHour + "&speed_ratio=0.6");
      setPred(r.data);
    } catch {
      toast.error("Prediction failed");
    }
  };

  useEffect(() => { refresh(); }, [refresh]);

  const counts = hotspots.reduce((acc, h) => {
    acc[h.congestion_label] = (acc[h.congestion_label] || 0) + 1;
    return acc;
  }, {});

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className={"text-base font-bold " + (darkMode ? "text-white" : "text-gray-800")}>
          Traffic Heatmap
        </h2>
        <button onClick={refresh} disabled={loading}
          className={"text-xs px-3 py-1.5 rounded-lg font-semibold transition-colors disabled:opacity-60 " +
            (darkMode ? "bg-gray-700 hover:bg-gray-600 text-white" : "bg-slate-100 hover:bg-slate-200 text-gray-700")}>
          {loading ? "..." : "Refresh"}
        </button>
      </div>

      {lastRefresh && (
        <p className={"text-[10px] mb-3 " + (darkMode ? "text-gray-500" : "text-gray-400")}>
          Last updated: {lastRefresh.toLocaleTimeString()} - {hotspots.length} hotspots
        </p>
      )}

      {Object.keys(counts).length > 0 && (
        <div className={card}>
          <div className={"text-xs font-semibold uppercase tracking-wide mb-2 " + (darkMode ? "text-gray-400" : "text-gray-500")}>
            Congestion Summary
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(counts).map(([cl, n]) => (
              <div key={cl} className="flex items-center gap-1.5">
                <span className={"w-2.5 h-2.5 rounded-full " + (CONGESTION_DOT[cl] || "bg-gray-400")} />
                <span className={"text-xs " + (darkMode ? "text-gray-300" : "text-gray-700")}>{cl}: <b>{n}</b></span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className={card}>
        <div className={"text-xs font-semibold uppercase tracking-wide mb-3 " + (darkMode ? "text-gray-400" : "text-gray-500")}>
          ML Congestion Prediction
        </div>
        <div className="flex gap-2 items-end mb-3">
          <div className="flex-1">
            <label className={lbl}>Hour of Day</label>
            <input type="number" min={0} max={23} value={predHour}
              onChange={e => setPredHour(Number(e.target.value))}
              className={"w-full px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 " +
                (darkMode ? "bg-gray-700 border-gray-600 text-white" : "bg-white border-slate-300 text-gray-900")} />
          </div>
          <button onClick={predictCongestion}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition-colors">
            Predict
          </button>
        </div>
        {prediction && (
          <div className="flex items-center justify-between">
            <div>
              <div className={"text-sm font-semibold " + (darkMode ? "text-white" : "text-gray-800")}>
                {prediction.label}
              </div>
              <div className={"text-xs " + (darkMode ? "text-gray-400" : "text-gray-500")}>
                Score: {Math.round((prediction.congestion_score || 0) * 100)}%
                {prediction.rush_hour && <span className="ml-2 text-orange-400"> Rush Hour</span>}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className={card}>
        <div className={"text-xs font-semibold uppercase tracking-wide mb-2 " + (darkMode ? "text-gray-400" : "text-gray-500")}>
          Map Legend
        </div>
        {Object.entries(CONGESTION_DOT).map(([cl, cls]) => (
          <div key={cl} className="flex items-center gap-2 py-1">
            <span className={"w-3 h-3 rounded-full " + cls} />
            <span className={"text-xs " + (darkMode ? "text-gray-300" : "text-gray-700")}>{cl}</span>
          </div>
        ))}
      </div>

      {hotspots.length > 0 && (
        <div>
          <div className={"text-xs font-semibold uppercase tracking-wide mb-2 " + (darkMode ? "text-gray-400" : "text-gray-500")}>
            Active Hotspots
          </div>
          {[...hotspots].sort((a, b) => (b.intensity || 0) - (a.intensity || 0)).slice(0, 10).map((h, i) => (
            <HotspotRow key={i} hotspot={h} dark={darkMode} />
          ))}
        </div>
      )}
    </div>
  );
}
