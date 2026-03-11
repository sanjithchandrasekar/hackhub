# 🚀 Quick Start Guide

## Fastest Way to Run the Project

### Option 1: Simple Demo (No Database)

1. **Install Backend**
```bash
cd backend
pip install fastapi uvicorn osmnx networkx geopandas shapely geopy scikit-learn pandas numpy requests
```

2. **Start Backend**
```bash
python main.py
```

3. **Install Frontend**
```bash
cd ../frontend
npm install
```

4. **Start Frontend**
```bash
npm start
```

5. **Open Browser**
Navigate to `http://localhost:3000`

### Option 2: Full Setup with Database

1. **Install PostgreSQL** (optional)
```bash
# Skip if you want to use SQLite
# Windows: Download from postgresql.org
# Mac: brew install postgresql
# Linux: sudo apt-get install postgresql postgresql-contrib postgis
```

2. **Setup Backend**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
```

3. **Initialize**
```bash
cd ../scripts
python init_db.py
```

4. **Start Services**
```bash
# Terminal 1: Backend
cd backend
python main.py

# Terminal 2: Frontend
cd frontend
npm start

# Terminal 3: Telemetry Simulator (optional)
cd scripts
python simulate_telemetry.py --once
```

## 🎮 Testing the Features

### Test Routing
1. Open app at `http://localhost:3000`
2. In "Route Planner" panel
3. Use default coordinates or enter new ones
4. Click "Calculate Route"
5. See route drawn on map

### Test Geocoding
1. Go to "Geocoding" panel
2. Tab: "Address → Coords"
3. Enter: "1600 Amphitheatre Parkway, Mountain View, CA"
4. Click "Find Coordinates"
5. See marker on map

### Test Geofence
1. Go to "Geofence Checker" panel
2. Enter Berkeley coordinates:
   - Latitude: 37.8719
   - Longitude: -122.2585
3. Click "Check Location"
4. See if inside UC Berkeley campus boundary

## 📊 API Testing with cURL

```bash
# Health check
curl http://localhost:8000/

# Calculate route
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"start_lat": 37.8719, "start_lon": -122.2585, "end_lat": 37.8690, "end_lon": -122.2560}'

# Check geofence
curl -X POST http://localhost:8000/geofence \
  -H "Content-Type: application/json" \
  -d '{"latitude": 37.8719, "longitude": -122.2585}'

# Geocode
curl -X POST http://localhost:8000/geocode \
  -H "Content-Type: application/json" \
  -d '{"address": "University of California, Berkeley"}'
```

## 🐛 Common Issues

### Backend won't start
- Check Python version: `python --version` (need 3.8+)
- Install missing packages: `pip install -r requirements.txt`

### Frontend errors
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again

### Map not showing
- Check if backend is running on port 8000
- Check browser console for CORS errors
- Try clearing browser cache

### OSM download slow
- This is normal for first run (2-5 minutes)
- Data is cached for future use
- Check `data/osm_data/` for cached files

## ⚡ Performance Tips

1. **Use cached OSM data**: Don't delete `data/osm_data/road_network.pkl`
2. **Limit telemetry**: Don't run simulator continuously for demos
3. **Use SQLite**: Faster setup, good for demos
4. **Close other tabs**: Map rendering can be CPU intensive

## 🎯 Demo Script

Perfect 5-minute demo flow:

1. **Introduction** (30 seconds)
   - Show architecture diagram
   - Explain key features

2. **Route Planning** (1 minute)
   - Calculate route between two points
   - Show distance and ETA
   - Highlight route on map

3. **Geocoding** (1 minute)
   - Search for an address
   - Show coordinates
   - Reverse geocode a point

4. **Geofence Detection** (1 minute)
   - Check a point inside campus
   - Check a point outside
   - Show distance to boundary

5. **Real-Time Learning** (1.5 minutes)
   - Run telemetry simulator
   - Show data being collected
   - Explain how models retrain

6. **Q&A** (30 seconds)

## 📱 Mobile Testing

The UI is responsive! Test on mobile:
1. Start backend and frontend
2. Find your local IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
3. Visit `http://YOUR_IP:3000` on mobile
4. Use "Current Location" button for GPS

## 🔧 Quick Fixes

### Reset Everything
```bash
# Delete data
rm -rf data/osm_data/*.pkl
rm -rf data/*.db
rm -rf models/*.pkl

# Reinitialize
python scripts/init_db.py
```

### Update Dependencies
```bash
# Backend
cd backend
pip install --upgrade -r requirements.txt

# Frontend
cd frontend
npm update
```

### Check Logs
```bash
# Backend logs are in console
# Check for errors in red

# Frontend logs
# Check browser console (F12)
```

## 🎨 Customization Quick Changes

### Change Map Center
Edit `frontend/src/components/MapView.jsx`:
```javascript
const defaultCenter = [YOUR_LAT, YOUR_LON];
```

### Change Color Theme
Edit `frontend/src/App.css`:
```css
.app-header {
  background: linear-gradient(135deg, #YOUR_COLOR1 0%, #YOUR_COLOR2 100%);
}
```

### Add Your Campus
Edit `data/campus_boundaries.json` and restart backend.

---

**Stuck? Check the main README.md for detailed troubleshooting!**
