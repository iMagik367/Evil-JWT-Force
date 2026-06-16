#!/bin/bash

echo "Building protected version of EVIL_JWT_FORCE..."

# Activate virtual environment if it exists
if [ -f "evil_jwt_env/bin/activate" ]; then
    source evil_jwt_env/bin/activate
fi

# Install required packages
python -m pip install -r requirements.txt

# Run the protected build
python scripts/build_protected.py

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "Build completed successfully!"
    echo "Protected version is available in build_protected directory"
else
    echo "Build failed!"
    exit 1
fi

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi 