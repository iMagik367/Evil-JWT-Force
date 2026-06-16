#!/bin/bash

echo "Launching Evil-Force-JWT AI Interface..."

# Create necessary directories if they don't exist
mkdir -p data
mkdir -p logs
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
python3 -c "import tkinter" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Installing tkinter..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y python3-tk
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3-tkinter
    elif command -v brew &> /dev/null; then
        brew install python-tk
    else
        echo "Please install tkinter manually for your distribution."
    fi
fi

python3 -c "import PIL" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Installing pillow..."
    pip3 install pillow
fi

# Run the AI interface
python3 gui/ai_interface.py

# Deactivate virtual environment if activated
if [ -f "venv/bin/activate" ]; then
    deactivate
fi

echo "AI Interface closed." 