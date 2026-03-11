# GeoEngine Enhanced - Quick Start Script
# Run this to start the complete enhanced GeoEngine platform

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   🌍 GeoEngine Enhanced v2.0.0" -ForegroundColor Green  
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Starting Enhanced GeoEngine Platform...`n" -ForegroundColor Yellow

# Check if we're in the right directory
if (!(Test-Path "backend") -or !(Test-Path "frontend")) {
    Write-Host "❌ Error: Please run this script from the geo-engine directory" -ForegroundColor Red
    exit 1
}

Write-Host "📋 Pre-flight Checks:" -ForegroundColor Cyan
Write-Host "   ✓ Backend directory found" -ForegroundColor Green
Write-Host "   ✓ Frontend directory found" -ForegroundColor Green

# Start Backend Server
Write-Host "`n🚀 Starting Backend Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python main.py"

Start-Sleep -Seconds 3

# Start Frontend Development Server
Write-Host "🎨 Starting Frontend Development Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm start"

Start-Sleep -Seconds 3

# Optionally start telemetry simulator
Write-Host "`n📡 Do you want to start the GPS telemetry simulator? (Y/N)" -ForegroundColor Cyan
$response = Read-Host

if ($response -eq 'Y' -or $response -eq 'y') {
    Write-Host "Starting Telemetry Simulator..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd scripts; python simulate_telemetry.py"
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   ✅ GeoEngine Enhanced is Starting!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "📡 Backend API:" -ForegroundColor Yellow
Write-Host "   http://localhost:8000" -ForegroundColor White
Write-Host "   http://localhost:8000/docs (API Documentation)`n" -ForegroundColor White

Write-Host "🌐 Frontend App:" -ForegroundColor Yellow
Write-Host "   http://localhost:3000`n" -ForegroundColor White

Write-Host "🎯 New Features:" -ForegroundColor Yellow
Write-Host "   • Dark Mode Toggle (🌙/☀️)" -ForegroundColor White
Write-Host "   • Traffic Heatmap" -ForegroundColor White
Write-Host "   • Route Analytics Dashboard" -ForegroundColor White
Write-Host "   • Live Asset Tracking" -ForegroundColor White
Write-Host "   • Favorite Routes" -ForegroundColor White
Write-Host "   • Distance & Area Measurement" -ForegroundColor White
Write-Host "   • POI Search" -ForegroundColor White
Write-Host "   • Alternative Routes`n" -ForegroundColor White

Write-Host "📖 Quick Tips:" -ForegroundColor Cyan
Write-Host "   1. Use the theme toggle in the header for dark mode" -ForegroundColor White
Write-Host "   2. Navigate between features using the tab buttons" -ForegroundColor White
Write-Host "   3. Click quick location badges for instant coordinates" -ForegroundColor White
Write-Host "   4. Enable auto-refresh in Traffic and Assets panels`n" -ForegroundColor White

Write-Host "Press any key to open browser windows..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')

# Open browser windows
Start-Process "http://localhost:8000/docs"
Start-Sleep -Seconds 2
Start-Process "http://localhost:3000"

Write-Host "`n🎉 All systems running! Enjoy GeoEngine Enhanced!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan
