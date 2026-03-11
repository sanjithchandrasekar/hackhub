# 🚀 ONE-COMMAND STARTUP GUIDE

## ⚡ Super Quick Start

### Option 1: Double-Click (Easiest)
```
📁 Just double-click: start.bat
```

### Option 2: PowerShell One-Liner
```powershell
cd e:\Projects\hackhub\geo-engine; .\run.ps1
```

### Option 3: Single PowerShell Command (Copy & Paste)
```powershell
cd e:\Projects\hackhub\geo-engine; Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\backend'; Write-Host 'BACKEND SERVER' -ForegroundColor Green; python main.py"; Start-Sleep 3; Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; Write-Host 'FRONTEND SERVER' -ForegroundColor Green; npm start"
```

---

## 📋 What Each Command Does

### ✅ start.bat (Recommended)
- ✅ Checks Python and Node.js
- ✅ Installs missing dependencies
- ✅ Starts backend in new window
- ✅ Starts frontend in new window
- ✅ Shows all URLs

### ✅ run.ps1
- ✅ PowerShell script version
- ✅ Colored output
- ✅ Starts both services
- ✅ Better for developers

### ✅ One-Liner Command
- ✅ Copy-paste and run
- ✅ No file execution needed
- ✅ Quick testing

---

## 🎯 After Running

You'll see **2 new terminal windows**:

**Window 1: Backend Server** (Green)
```
BACKEND SERVER (Port 8000)
API: http://localhost:8000
Docs: http://localhost:8000/docs
```

**Window 2: Frontend Server** (Yellow)
```
FRONTEND SERVER (Port 3000)
App: http://localhost:3000
```

---

## 🌐 Access the Application

**Main App:** http://localhost:3000  
**API Docs:** http://localhost:8000/docs  
**Health:** http://localhost:8000

Browser auto-opens when ready! 🎉

---

## ⏱️ Wait Times

**First Run:** 2-5 minutes (downloading OpenStreetMap data)  
**Future Runs:** ~10 seconds (data cached)

---

## 🛑 Stop the Services

**Option 1:** Close both terminal windows  
**Option 2:** Press `Ctrl+C` in each window

---

## 🔧 Prerequisites

Before running, ensure you have:
- ✅ Python 3.8+ installed
- ✅ Node.js 14+ installed
- ✅ Internet connection (for first run)

Check with:
```powershell
python --version
node --version
```

---

## 📦 Manual Installation (If Needed)

If auto-install fails:

**Backend:**
```powershell
cd backend
pip install fastapi uvicorn osmnx networkx geopandas shapely geopy scikit-learn pandas numpy psycopg2-binary requests
```

**Frontend:**
```powershell
cd frontend
npm install
```

---

## 🐛 Troubleshooting

### Port Already in Use
```powershell
# Kill process on port 8000
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process

# Kill process on port 3000
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process
```

### Python/Node Not Found
- Install Python: https://python.org
- Install Node.js: https://nodejs.org

### Dependencies Fail to Install
```powershell
# Update pip first
python -m pip install --upgrade pip

# Then run start.bat again
```

---

## 🎬 Complete One-Command Example

Copy and paste this entire command:

```powershell
cd e:\Projects\hackhub\geo-engine; Write-Host "`n🚀 Starting Intelligent Geospatial Engine...`n" -ForegroundColor Cyan; Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; Write-Host '========================================' -ForegroundColor Green; Write-Host '  BACKEND: http://localhost:8000' -ForegroundColor Yellow; Write-Host '========================================' -ForegroundColor Green; python main.py"; Start-Sleep -Seconds 3; Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; Write-Host '========================================' -ForegroundColor Green; Write-Host '  FRONTEND: http://localhost:3000' -ForegroundColor Yellow; Write-Host '========================================' -ForegroundColor Green; npm start"; Write-Host "✅ Services starting in 2 windows!" -ForegroundColor Green; Write-Host "📍 Frontend: http://localhost:3000" -ForegroundColor White; Write-Host "📍 Backend: http://localhost:8000`n" -ForegroundColor White
```

---

## 📸 What You'll See

After running, you get:
1. ✅ Backend terminal showing API logs
2. ✅ Frontend terminal showing React build
3. ✅ Browser auto-opens to http://localhost:3000
4. ✅ Interactive map ready to use!

---

## 🎯 Quick Test Commands

Test if services are running:

```powershell
# Test backend
curl http://localhost:8000

# Test frontend (in browser)
# Visit: http://localhost:3000
```

---

## 💡 Pro Tips

1. **Keep both windows open** - closing them stops the services
2. **First run takes longer** - downloading map data
3. **Check terminal colors**:
   - Green = Backend
   - Yellow = Frontend
4. **Set firewall rules** if prompted by Windows

---

## ✨ You're Ready!

Just run: `start.bat` or paste the one-liner command! 🎉
