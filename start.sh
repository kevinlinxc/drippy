#!/bin/bash

# Script to start both backend and frontend

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Drippy Backend and Frontend...${NC}\n"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Please run setup first:"
    echo "  uv venv --seed --python 3.12"
    echo "  source .venv/bin/activate"
    echo "  uv pip install -e ."
    exit 1
fi

# Check if node_modules exists in my-electron-app
if [ ! -d "my-electron-app/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd my-electron-app
    npm install
    cd ..
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}Shutting down...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Start backend
echo -e "${GREEN}Starting backend server on http://localhost:8000${NC}"
source .venv/bin/activate
uvicorn drippy.api:app --reload &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend
echo -e "${GREEN}Starting Electron frontend...${NC}"
cd my-electron-app
npm start &
FRONTEND_PID=$!
cd ..

echo -e "\n${BLUE}Both services are running!${NC}"
echo -e "${BLUE}Backend API: http://localhost:8000${NC}"
echo -e "${BLUE}API Docs: http://localhost:8000/docs${NC}"
echo -e "${BLUE}Press Ctrl+C to stop both services${NC}\n"

# Wait for both processes
wait


