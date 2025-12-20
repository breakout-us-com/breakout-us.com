#!/bin/bash

# O'Neil Breakout Website - Run Script

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting O'Neil Breakout Website..."

# Start Backend
echo "Starting FastAPI Backend..."
cd "$PROJECT_DIR/backend"
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"

# Wait for backend to be ready
sleep 2

# Start Frontend
echo "Starting Next.js Frontend..."
cd "$PROJECT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "==================================="
echo "O'Neil Breakout Website is running!"
echo "==================================="
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Handle shutdown
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

# Wait for processes
wait
