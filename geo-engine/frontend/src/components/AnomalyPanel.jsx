import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import toast from "react-hot-toast";

function AnomalyCard({ anomaly, dark }) {
  const ts = anomaly.detected_at
    ? new Date(anomaly.detected_at).toLocaleTimeString()
    : "--:--:--";
  return (
    <div className={`rounded-xl border px-4 py-3 mb-2 border-l-4 border-l-red-500
      ${dark ? "bg-gray-800 border-gray-700" : "bg-white border-slate-200 shadow-sm"}`}>
      <div className="flex items-start justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className="text-base">⚠️</span>
          <span className={`font-semibold text-sm ${dark ? "text-white" : "text-gray-800"}`}>
            {anomaly.asset_id || "Unknown Asset"}
          </span>
        </div>
        <span className={`text-[10px] ${dark ? "text-gray-400" : "text-gray-400"}`}>{ts}</span>
      </div>
      <div className={`text-xs ${dark ? "text-gray-300" : "text-gray-700"} mb-1`}>
        {anomaly.reason || "Abnormal traffic pattern detected"}
      </div>
      <div className={`flex gap-4 text-[11px] ${dark ? "text-gray-400" : "text-gray-500"}`}>
        {anomaly.speed_kmh != null && (
          <span>Speed: <b>{typeof anomaly.speed_kmh === "number" ? anomaly.speed_kmh.toFixed(1) : anomaly.speed_kmh} km/h</b></span>
        )}
        {anomaly.lat != null && (
          <span>Loc: {anomaly.lat.toFixed(4)}, {anomaly.lon.toFixed(4)}</span>
        )}
        {anomaly.score != null && (
          <span>Score: {typeof anomaly.score === "number" ? anomaly.score.toFixed(3) : anomaly.score}</span>
        )}
      </div>
    </div>
  );
}

export default function AnomalyPanel({ darkMode, onAnomaliesLoaded }) {
  const [anomalies, setAnomalies] = useState([]);
  const [loading,   setLoading]   = useState(false);
  const [lastRefresh, setLast]    = useState(null);
  const [filter,    setFilter]    = useState("all");   // all | recent

  const card = "rounded-xl border p-4 mb-3 " + (darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-slate-200 shadow-sm");

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const r = await axios.get("/anomalies");
      const list = r.data.anomalies || [];
      setAnomalies(list);
      setLast(new Date());
      if (onAnomaliesLoaded) onAnomaliesLoaded(list);
    } catch {
      toast.error("Failed to fetch anomalies");
    } finally {
      setLoading(false);
    }
  }, [onAnomaliesLoaded]);

  useEffect(() => { refresh(); }, [refresh]);

  const displayed = filter === "recent"
    ? anomalies.slice(-10).reverse()
    : [...anomalies].reverse();

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className={"text-base font-bold " + (darkMode ? "text-white" : "text-gray-800")}>
          Anomaly Feed
        </h2>
        <button onClick={refresh} disabled={loading}
          className={"text-xs px-3 py-1.5 rounded-lg font-semibold transition-colors disabled:opacity-60 " +
            (darkMode ? "bg-gray-700 hover:bg-gray-600 text-white" : "bg-slate-100 hover:bg-slate-200 text-gray-700")}>
          {loading ? "..." : "Refresh"}
        </button>
      </div>

      {lastRefresh && (
        <p className={"text-[10px] mb-3 " + (darkMode ? "text-gray-500" : "text-gray-400")}>
          Last: {lastRefresh.toLocaleTimeString()} &nbsp;·&nbsp; {anomalies.length} total anomalies
        </p>
      )}

      {/* Summary card */}
      <div className={card}>
        <div className="grid grid-cols-3 gap-3 text-center">
          {[
            { val: anomalies.length,          lbl: "Total" },
            { val: displayed.slice(0, 24).length, lbl: "Shown" },
            { val: anomalies.filter(a => {
                if (!a.detected_at) return false;
                const diff = Date.now() - new Date(a.detected_at).getTime();
                return diff < 3600000;
              }).length, lbl: "Last Hour" },
          ].map(({ val, lbl }) => (
            <div key={lbl}>
              <div className={"text-xl font-bold " + (darkMode ? "text-white" : "text-gray-800")}>{val}</div>
              <div className={"text-[10px] " + (darkMode ? "text-gray-500" : "text-gray-400")}>{lbl}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Filter */}
      <div className="flex gap-2 mb-4">
        {["all", "recent"].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={"flex-1 py-1.5 rounded-lg text-xs font-semibold capitalize transition-colors " +
              (filter === f
                ? "bg-red-600 text-white"
                : darkMode ? "bg-gray-700 text-gray-300" : "bg-slate-100 text-gray-600")}>
            {f === "all" ? "All" : "Recent 10"}
          </button>
        ))}
      </div>

      {/* Anomaly list */}
      {displayed.length > 0 ? (
        displayed.map((a, i) => (
          <AnomalyCard key={i} anomaly={a} dark={darkMode} />
        ))
      ) : (
        <div className={"rounded-xl border p-6 text-center " + (darkMode ? "bg-gray-800 border-gray-700 text-gray-400" : "bg-slate-50 border-slate-200 text-gray-400")}>
          <div className="text-3xl mb-2">✅</div>
          <div className="text-sm font-semibold">No anomalies detected</div>
          <div className="text-xs mt-1">Send telemetry data to detect traffic anomalies.</div>
        </div>
      )}
    </div>
  );
}
