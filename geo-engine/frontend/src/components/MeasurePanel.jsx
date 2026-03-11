import React, { useState } from 'react';
import axios from 'axios';

function MeasurePanel({ onMeasureUpdate, darkMode }) {
  const [points, setPoints] = useState([]);
  const [measureType, setMeasureType] = useState('distance');
  const [result, setResult] = useState(null);
  const [message, setMessage] = useState('');

  const addPoint = () => {
    const newPoint = {
      lat: 12.9716 + (Math.random() - 0.5) * 0.1,
      lon: 77.5946 + (Math.random() - 0.5) * 0.1
    };
    const newPoints = [...points, newPoint];
    setPoints(newPoints);
    if (onMeasureUpdate) {
      onMeasureUpdate(newPoints);
    }
  };

  const removePoint = (index) => {
    const newPoints = points.filter((_, i) => i !== index);
    setPoints(newPoints);
    if (onMeasureUpdate) {
      onMeasureUpdate(newPoints);
    }
    setResult(null);
  };

  const clearAll = () => {
    setPoints([]);
    setResult(null);
    if (onMeasureUpdate) {
      onMeasureUpdate([]);
    }
  };

  const calculate = async () => {
    if (measureType === 'distance' && points.length < 2) {
      setMessage('Add at least 2 points for distance measurement');
      return;
    }
    if (measureType === 'area' && points.length < 3) {
      setMessage('Add at least 3 points for area measurement');
      return;
    }

    try {
      const response = await axios.post('/measure', {
        points: points,
        measurement_type: measureType
      });
      setResult(response.data);
      setMessage('');
    } catch (error) {
      setMessage('Measurement failed');
      console.error(error);
    }
  };

  const updatePoint = (index, field, value) => {
    const newPoints = [...points];
    newPoints[index][field] = parseFloat(value) || 0;
    setPoints(newPoints);
    if (onMeasureUpdate) {
      onMeasureUpdate(newPoints);
    }
  };

  return (
    <div className="card">
      <h3 className="card-title">📏 Measurement Tools</h3>
      
      <div className="form-group">
        <label className="form-label">Measurement Type</label>
        <select 
          className="form-input"
          value={measureType}
          onChange={(e) => {
            setMeasureType(e.target.value);
            setResult(null);
          }}
        >
          <option value="distance">Distance (Path)</option>
          <option value="area">Area (Polygon)</option>
        </select>
      </div>

      <div className="btn-group">
        <button className="btn btn-primary" onClick={addPoint}>
          ➕ Add Point
        </button>
        <button className="btn btn-danger" onClick={clearAll} disabled={points.length === 0}>
          🗑️ Clear All
        </button>
      </div>

      {points.length > 0 && (
        <div className="mt-2">
          <h4 style={{ fontSize: '14px', marginBottom: '8px', color: 'var(--text-primary)' }}>
            Points ({points.length})
          </h4>
          {points.map((point, index) => (
            <div key={index} className="flex gap-1 mb-1" style={{ alignItems: 'center' }}>
              <span style={{ fontSize: '12px', minWidth: '20px' }}>{index + 1}.</span>
              <input 
                type="number"
                step="0.0001"
                className="form-input"
                value={point.lat}
                onChange={(e) => updatePoint(index, 'lat', e.target.value)}
                placeholder="Lat"
                style={{ fontSize: '12px' }}
              />
              <input 
                type="number"
                step="0.0001"
                className="form-input"
                value={point.lon}
                onChange={(e) => updatePoint(index, 'lon', e.target.value)}
                placeholder="Lon"
                style={{ fontSize: '12px' }}
              />
              <button 
                className="btn btn-danger"
                onClick={() => removePoint(index)}
                style={{ padding: '8px', fontSize: '12px' }}
              >
                ❌
              </button>
            </div>
          ))}
        </div>
      )}

      {points.length >= (measureType === 'area' ? 3 : 2) && (
        <button className="btn btn-secondary mt-2" onClick={calculate}>
          📐 Calculate {measureType === 'area' ? 'Area' : 'Distance'}
        </button>
      )}

      {result && result.type === 'distance' && (
        <div className="alert alert-success mt-2">
          <strong>📏 Total Distance:</strong><br/>
          {result.distance_km} km<br/>
          {result.distance_m} meters
        </div>
      )}

      {result && result.type === 'area' && (
        <div className="alert alert-success mt-2">
          <strong>📐 Total Area:</strong><br/>
          {result.area_km2} km²<br/>
          {result.area_m2} m²<br/>
          {result.area_hectares} hectares
        </div>
      )}

      {message && (
        <div className="alert alert-warning mt-2">
          {message}
        </div>
      )}

      {points.length === 0 && (
        <div className="alert alert-info mt-2">
          Add points to measure distance or area. You can manually edit coordinates or click on the map.
        </div>
      )}
    </div>
  );
}

export default MeasurePanel;
