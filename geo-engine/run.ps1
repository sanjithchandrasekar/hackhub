#!/usr/bin/env pwsh
# Intelligent Geospatial Engine - One-Click Startup Script

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Intelligent Geospatial Engine - Starting Services...   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Get project root directory
$ProjectRoot = $PSScriptRoot

# Start Backend Server
Write-Host "🚀 Starting Backend Server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot\backend'; Write-Host '========================================' -ForegroundColor Cyan; Write-Host '       BACKEND SERVER (Port 8000)' -ForegroundColor Green; Write-Host '========================================' -ForegroundColor Cyan; Write-Host 'API: http://localhost:8000' -ForegroundColor Yellow; Write-Host 'Docs: http://localhost:8000/docs' -ForegroundColor Yellow; Write-Host '========================================`n' -ForegroundColor Cyan; python main.py"

# Wait 3 seconds for backend to initialize
Write-Host "⏳ Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start Frontend Server
Write-Host "🎨 Starting Frontend Server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot\frontend'; Write-Host '========================================' -ForegroundColor Cyan; Write-Host '      FRONTEND SERVER (Port 3000)' -ForegroundColor Green; Write-Host '========================================' -ForegroundColor Cyan; Write-Host 'App: http://localhost:3000' -ForegroundColor Yellow; Write-Host '========================================`n' -ForegroundColor Cyan; npm start"

# Summary
Write-Host "`n✅ Services are starting in separate windows!`n" -ForegroundColor Green
Write-Host "📍 URLs:" -ForegroundColor Cyan
Write-Host "   Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "   Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "`n⏱️  First run: Wait 2-5 min for OSM data download" -ForegroundColor Yellow
Write-Host "🌐 Browser will auto-open when frontend is ready`n" -ForegroundColor Yellow
Write-Host "Press any key to exit this launcher..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
