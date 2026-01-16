#!/bin/bash

# Modern Celebrity Face Match - Startup Script
# This script helps you start the new FastAPI + React demo
# NOTE: Assumes Redis is already running locally with your data

set -e

echo "=========================================="
echo "🎭 Celebrity Face Match - Modern UI"
echo "=========================================="
echo ""

# Check Redis first
echo "Checking prerequisites..."
if ! redis-cli ping &> /dev/null; then
    echo "❌ Redis is not running!"
    echo "   Please start your local Redis first."
    exit 1
fi
echo "✅ Redis is running"

# Check if vector index exists
if ! redis-cli FT._LIST 2>/dev/null | grep -q "celeb_faces_idx"; then
    echo "⚠️  Warning: Vector index 'celeb_faces_idx' not found"
    echo "   You may need to run: python build_vector_db.py"
fi

echo ""
echo "Choose how to run the demo:"
echo ""
echo "  1. 💻 Local Development (Recommended - Easy to debug)"
echo "  2. 🐳 Docker (Backend + Frontend in containers)"
echo "  3. 🔧 Backend Only (for testing)"
echo "  4. 🎨 Frontend Only (backend must be running)"
echo ""

read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "💻 Starting Local Development Mode..."
        echo "=========================================="
        echo ""
        echo "This will open 2 terminal windows:"
        echo "  1. FastAPI Backend"
        echo "  2. React Frontend"
        echo ""

        # Start backend
        echo "🔵 Starting Backend..."
        osascript -e 'tell app "Terminal" to do script "cd \"'$(pwd)'/backend\" && pip install -r requirements.txt && python main.py"' &

        sleep 3

        # Start frontend
        echo "🟢 Starting Frontend..."
        osascript -e 'tell app "Terminal" to do script "cd \"'$(pwd)'/frontend\" && npm install && npm run dev"' &

        echo ""
        echo "✅ All services starting..."
        echo ""
        echo "📍 Access points:"
        echo "   Frontend:    http://localhost:3000"
        echo "   Backend API: http://localhost:8000"
        echo "   Redis:       localhost:6379 (your existing instance)"
        echo ""
        sleep 3
        if command -v open &> /dev/null; then
            open http://localhost:3000
        fi
        ;;

    2)
        echo ""
        echo "🐳 Starting with Docker..."
        echo "=========================================="
        echo ""
        echo "Note: Docker containers will connect to your local Redis"
        echo ""

        # Start services
        docker-compose up -d

        echo ""
        echo "✅ Services started!"
        echo ""
        echo "📍 Access points:"
        echo "   Frontend:     http://localhost:3000"
        echo "   Backend API:  http://localhost:8000"
        echo "   Redis:        localhost:6379 (your existing instance)"
        echo ""
        echo "📊 View logs:"
        echo "   docker-compose logs -f"
        echo ""
        echo "🛑 Stop services:"
        echo "   docker-compose down"
        echo ""

        sleep 3
        if command -v open &> /dev/null; then
            open http://localhost:3000
        fi
        ;;

    3)
        echo ""
        echo "🔧 Starting Backend Only..."
        echo "=========================================="
        cd backend
        
        if [ ! -d "venv" ]; then
            echo "Creating virtual environment..."
            python3 -m venv venv
        fi
        
        source venv/bin/activate
        pip install -r requirements.txt
        
        echo ""
        echo "✅ Starting FastAPI server..."
        python main.py
        ;;
        
    4)
        echo ""
        echo "🎨 Starting Frontend Only..."
        echo "=========================================="
        cd frontend
        
        if [ ! -d "node_modules" ]; then
            echo "Installing dependencies..."
            npm install
        fi
        
        echo ""
        echo "✅ Starting Vite dev server..."
        npm run dev
        ;;
        
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

