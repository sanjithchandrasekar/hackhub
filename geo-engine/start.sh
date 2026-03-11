#!/bin/bash

echo "================================================"
echo "Intelligent Geospatial Engine - Quick Start"
echo "================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "Creating virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing backend dependencies..."
    pip install -r requirements.txt
    cd ..
else
    echo "Virtual environment found."
fi

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
else
    echo "Frontend dependencies found."
fi

echo ""
echo "================================================"
echo "Starting Backend Server..."
echo "================================================"

# Start backend in new terminal
cd backend
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell app "Terminal" to do script "cd '"$PWD"' && source venv/bin/activate && python main.py"'
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash -c "source venv/bin/activate && python main.py; exec bash"
    elif command -v xterm &> /dev/null; then
        xterm -e "source venv/bin/activate && python main.py" &
    else
        echo "Warning: Could not open new terminal. Run 'cd backend && source venv/bin/activate && python main.py' manually"
    fi
fi
cd ..

echo ""
echo "Waiting for backend to start..."
sleep 5

echo ""
echo "================================================"
echo "Starting Frontend Development Server..."
echo "================================================"

# Start frontend in new terminal
cd frontend
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell app "Terminal" to do script "cd '"$PWD"' && npm start"'
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash -c "npm start; exec bash"
    elif command -v xterm &> /dev/null; then
        xterm -e "npm start" &
    else
        echo "Warning: Could not open new terminal. Run 'cd frontend && npm start' manually"
    fi
fi
cd ..

echo ""
echo "================================================"
echo "Services Starting!"
echo "================================================"
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Check the new terminal windows for server output."
