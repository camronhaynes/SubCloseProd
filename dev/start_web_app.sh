#!/bin/bash

# Late Interest Calculator - Web App Startup Script
# This script helps you start both the backend and frontend servers

echo "================================================================================"
echo "           Late Interest Calculator - Web App Startup"
echo "================================================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "late_interest_engine.py" ]; then
    echo "Error: Please run this script from the SubCloseProd directory"
    exit 1
fi

echo "This script will help you start the web application."
echo ""
echo "You need TWO terminal windows:"
echo "  1. Backend (Flask API server)"
echo "  2. Frontend (Next.js web UI)"
echo ""
echo "================================================================================"
echo ""

# Ask which component to start
echo "Which component do you want to start?"
echo "  1) Backend API (Flask)"
echo "  2) Frontend UI (Next.js)"
echo "  3) Run API test (verify backend is working)"
echo ""
read -p "Enter choice (1, 2, or 3): " choice

case $choice in
    1)
        echo ""
        echo "Starting Flask API Backend..."
        echo "================================================================================"
        cd backend/app/api
        python3 server.py
        ;;
    2)
        echo ""
        echo "Starting Next.js Frontend..."
        echo "================================================================================"
        echo "First, checking if node_modules exists..."
        if [ ! -d "frontend/node_modules" ]; then
            echo "Installing dependencies (first time only)..."
            cd frontend
            npm install
        else
            echo "Dependencies already installed."
            cd frontend
        fi
        echo ""
        echo "Starting development server..."
        npm run dev
        ;;
    3)
        echo ""
        echo "Running API Test..."
        echo "================================================================================"
        echo "Note: Make sure the Flask server is running in another terminal!"
        echo ""
        sleep 2
        python3 test_web_api.py
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
