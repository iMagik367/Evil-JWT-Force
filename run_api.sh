#!/bin/bash

echo "Launching Evil-Force-JWT API Server..."

# Create necessary directories if they don't exist
mkdir -p data
mkdir -p logs
mkdir -p api
mkdir -p ai_system/logs

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "Virtual environment activated."
else
    echo "No virtual environment found. Continuing without activation."
fi

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in the PATH."
    echo "Please install Python 3.7 or higher."
    exit 1
fi

# Install required packages if missing
echo "Checking required packages..."
python3 -c "import flask" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Installing Flask..."
    pip3 install flask flask-cors
fi

# Set port (default: 5000)
PORT=5000
if [ ! -z "$1" ]; then
    PORT=$1
fi

# Run the API server
echo "Starting API server on port $PORT..."
export PORT=$PORT
python3 api/jwt_api.py

# Deactivate virtual environment if activated
if [ -f "venv/bin/activate" ]; then
    deactivate
fi

echo "API Server stopped." 