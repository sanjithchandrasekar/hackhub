import React, { useState, useEffect } from 'react';
import axios from 'axios';

function AssetTracker({ onAssetsUpdate, darkMode }) {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchAssets = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/assets/live');
      setAssets(response.data.assets || []);
      if (onAssetsUpdate) {
        onAssetsUpdate(response.data.assets || []);
      }
    } catch (error) {
      console.error('Failed to fetch assets:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchAssets, 5000); // Refresh every 5 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getStatusColor = (status) => {
    switch(status) {
      case 'MOVING': return 'success';
      case 'IDLE': return 'warning';
      case 'SPEEDING': return 'danger';
      default: return 'info';
    }
  };

  return (
    <div className="card">
      <h3 className="card-title">📡 Live Asset Tracking</h3>
      
      <div className="flex-between mb-2">
        <div>
          <span className="badge badge-info">{assets.length} Active Assets</span>
        </div>
        <button 
          className={`btn ${autoRefresh ? 'btn-secondary' : 'btn-outline'}`}
          onClick={() => setAutoRefresh(!autoRefresh)}
          style={{ padding: '6px 12px', fontSize: '12px' }}
        >
          {autoRefresh ? '⏸️ Pause' : '▶️ Auto'}
        </button>
      </div>

      {loading && assets.length === 0 && (
        <div className="flex-center" style={{ padding: '20px' }}>
          <div className="spinner"></div>
        </div>
      )}

      {assets.length > 0 && (
        <div>
          {assets.map((asset, index) => (
            <div 
              key={index}
              className="list-item"
              style={{ 
                background: 'var(--bg-secondary)',
                marginBottom: '8px',
                borderRadius: '8px'
              }}
            >
              <div className="flex-between mb-1">
                <strong style={{ fontSize: '14px' }}>{asset.asset_id}</strong>
                <span className={`badge badge-${getStatusColor(asset.status)}`}>
                  {asset.status}
                </span>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                <div>📍 Position: {asset.current_position?.lat.toFixed(4)}, {asset.current_position?.lon.toFixed(4)}</div>
                <div>⚡ Speed: {asset.speed.toFixed(1)} km/h</div>
                <div>🧭 Heading: {asset.heading}°</div>
                <div>📊 Reports: {asset.total_reports}</div>
                {asset.last_update && (
                  <div>🕐 Updated: {new Date(asset.last_update).toLocaleTimeString()}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {assets.length === 0 && !loading && (
        <div className="alert alert-info">
          No active assets. Start the telemetry simulator to see live tracking!
          <br/><br/>
          <code style={{ fontSize: '11px' }}>cd scripts && python simulate_telemetry.py</code>
        </div>
      )}
    </div>
  );
}

export default AssetTracker;
