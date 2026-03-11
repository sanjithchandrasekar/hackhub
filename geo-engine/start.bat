@echo off
title Intelligent Geospatial Engine - Launcher
color 0B

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   Intelligent Geospatial Engine - Starting Services...   ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Go to script directory
cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

REM Check Node
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found! Please install Node.js from nodejs.org
    pause
    exit /b 1
)

REM Install backend dependencies if needed
echo 🔧 Checking backend dependencies...
cd backend
python -m pip install fastapi uvicorn osmnx networkx geopandas shapely geopy scikit-learn pandas numpy psycopg2-binary requests --quiet
cd ..

REM Install frontend dependencies if needed
if not exist "frontend\node_modules\" (
    echo 📦 Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

echo.
echo 🚀 Starting Backend Server...
cd backend
start "Backend API (Port 8000)" cmd /k "color 0A && echo ======================================== && echo        BACKEND SERVER (Port 8000) && echo ======================================== && echo API: http://localhost:8000 && echo Docs: http://localhost:8000/docs && echo ======================================== && echo. && python main.py"
cd ..

echo ⏳ Waiting for backend to initialize...
timeout /t 3 /nobreak > nul

echo.
echo 🎨 Starting Frontend Server...
cd frontend
start "Frontend App (Port 3000)" cmd /k "color 0E && echo ======================================== && echo       FRONTEND SERVER (Port 3000) && echo ======================================== && echo App: http://localhost:3000 && echo ======================================== && echo. && npm start"
cd ..

echo.
echo ✅ Services are starting in separate windows!
echo.
echo 📍 URLs:
echo    Frontend:  http://localhost:3000
echo    Backend:   http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo.
echo ⏱️  First run: Wait 2-5 min for OSM data download
echo 🌐 Browser will auto-open when frontend is ready
echo.
echo Press any key to exit this launcher...
pause > nul
