#!/bin/bash

# Simple one-command startup for the modern demo
# Assumes Redis is already running locally

echo "🎭 Starting Celebrity Face Match - Modern UI"
echo ""

# Quick Redis check
if ! redis-cli ping &> /dev/null; then
    echo "❌ Error: Redis is not running"
    echo "Please start your local Redis instance first"
    exit 1
fi

echo "✅ Redis detected"
echo ""
echo "Starting services..."
echo ""

# Start backend in background
echo "🔵 Starting backend..."
cd backend
pip install -q -r requirements.txt 2>/dev/null
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo "🟢 Starting frontend..."
cd frontend
npm install --silent 2>/dev/null
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Services started!"
echo ""
echo "📍 Access the demo at: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait

