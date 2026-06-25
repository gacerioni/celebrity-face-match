#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
REDIS_PORT="${REDIS_PORT:-6379}"

# Ensure venv exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Creating virtualenv..."
    python3 -m venv "$SCRIPT_DIR/.venv"
    "$SCRIPT_DIR/.venv/bin/pip" install -q -r "$SCRIPT_DIR/backend/requirements.txt"
fi

# Redis check
if ! redis-cli -p "$REDIS_PORT" ping &>/dev/null; then
    echo "Error: Redis not responding on port $REDIS_PORT"
    exit 1
fi
echo "Redis ok on port $REDIS_PORT"

# Backend
echo "Starting backend..."
cd "$SCRIPT_DIR"
REDIS_PORT="$REDIS_PORT" "$VENV_PYTHON" backend/main.py &
BACKEND_PID=$!

sleep 3

# Frontend
echo "Starting frontend..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Demo running:"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
