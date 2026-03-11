import React, { useState, useEffect } from 'react';
import axios from 'axios';

function FavoritesPanel({ onRouteCalculated, darkMode }) {
  const [favorites, setFavorites] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    start_lat: '12.9716',
    start_lon: '77.5946',
    end_lat: '12.9350',
    end_lon: '77.6244',
    notes: ''
  });

  useEffect(() => {
    fetchFavorites();
  }, []);

  const fetchFavorites = async () => {
    try {
      const response = await axios.get('/favorites');
      setFavorites(response.data.favorites || []);
    } catch (error) {
      console.error('Failed to fetch favorites:', error);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/favorites', formData);
      setShowAddForm(false);
      setFormData({
        name: '',
        start_lat: '12.9716',
        start_lon: '77.5946',
        end_lat: '12.9350',
        end_lon: '77.6244',
        notes: ''
      });
      fetchFavorites();
    } catch (error) {
      console.error('Failed to add favorite:', error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`/favorites/${id}`);
      fetchFavorites();
    } catch (error) {
      console.error('Failed to delete favorite:', error);
    }
  };

  const handleLoadRoute = async (favorite) => {
    try {
      const response = await axios.post('/route', {
        start_lat: favorite.start_lat,
        start_lon: favorite.start_lon,
        end_lat: favorite.end_lat,
        end_lon: favorite.end_lon
      });
      if (onRouteCalculated && response.data.route) {
        onRouteCalculated(response.data.route);
      }
    } catch (error) {
      console.error('Failed to load route:', error);
    }
  };

  return (
    <div className="card">
      <h3 className="card-title">⭐ Favorite Routes</h3>
      
      <button 
        className="btn btn-primary"
        onClick={() => setShowAddForm(!showAddForm)}
      >
        {showAddForm ? '❌ Cancel' : '➕ Add Favorite'}
      </button>

      {showAddForm && (
        <form onSubmit={handleAdd} className="mt-2">
          <div className="form-group">
            <label className="form-label">Route Name</label>
            <input 
              type="text"
              className="form-input"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
              placeholder="e.g., Home to Office"
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">Start Lat / Lon</label>
            <div className="flex gap-1">
              <input 
                type="number"
                step="0.0001"
                className="form-input"
                value={formData.start_lat}
                onChange={(e) => setFormData({...formData, start_lat: e.target.value})}
                required
              />
              <input 
                type="number"
                step="0.0001"
                className="form-input"
                value={formData.start_lon}
                onChange={(e) => setFormData({...formData, start_lon: e.target.value})}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">End Lat / Lon</label>
            <div className="flex gap-1">
              <input 
                type="number"
                step="0.0001"
                className="form-input"
                value={formData.end_lat}
                onChange={(e) => setFormData({...formData, end_lat: e.target.value})}
                required
              />
              <input 
                type="number"
                step="0.0001"
                className="form-input"
                value={formData.end_lon}
                onChange={(e) => setFormData({...formData, end_lon: e.target.value})}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Notes (optional)</label>
            <input 
              type="text"
              className="form-input"
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              placeholder="Add notes..."
            />
          </div>

          <button type="submit" className="btn btn-secondary">
            💾 Save Favorite
          </button>
        </form>
      )}

      {favorites.length > 0 && (
        <div className="mt-2">
          {favorites.map((fav, index) => (
            <div 
              key={fav.id || index}
              className="list-item"
              style={{ 
                background: 'var(--bg-secondary)',
                marginBottom: '8px',
                borderRadius: '8px'
              }}
            >
              <div className="flex-between mb-1">
                <strong>{fav.name}</strong>
              </div>
              {fav.notes && (
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  {fav.notes}
                </div>
              )}
              <div className="flex gap-1">
                <button 
                  className="btn btn-outline"
                  style={{ padding: '6px 12px', fontSize: '12px' }}
                  onClick={() => handleLoadRoute(fav)}
                >
                  🗺️ Load Route
                </button>
                <button 
                  className="btn btn-danger"
                  style={{ padding: '6px 12px', fontSize: '12px' }}
                  onClick={() => handleDelete(fav.id)}
                >
                  🗑️ Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {favorites.length === 0 && !showAddForm && (
        <div className="alert alert-info mt-2">
          No saved routes yet. Add your frequently used routes as favorites!
        </div>
      )}
    </div>
  );
}

export default FavoritesPanel;
