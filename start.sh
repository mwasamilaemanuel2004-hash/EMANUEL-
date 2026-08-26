#!/bin/bash

echo "============================================"
echo "   ESMH.TRADE Backend Startup"
echo "============================================"

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create data directory
mkdir -p ../data/logs

# Start server
echo "Starting ESMH.TRADE API..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
