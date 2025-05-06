#!/bin/bash

# Script to run the Streamlit viewer app with the correct Python environment
# Avoids conflicts with system Python/Anaconda installations

# Make the script executable if it's not already
if [ ! -x "$0" ]; then
    chmod +x "$0"
    echo "Made script executable."
fi

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "Using local virtual environment (.venv)"
    
    # Activate the virtual environment
    source .venv/bin/activate
    
    # Use the specific streamlit from the virtual environment
    STREAMLIT_PATH=".venv/bin/streamlit"
    
    # Run the Streamlit app
    echo "Starting Tweet Viewer app..."
    echo "If the browser doesn't open automatically, go to: http://localhost:8501"
    
    # Run with the explicit streamlit path to avoid using system Python
    $STREAMLIT_PATH run tweet_viewer.py
    
    # Deactivate the virtual environment when done
    deactivate
else
    echo "Virtual environment (.venv) not found."
    echo "Please ensure you've set up the project properly:"
    echo "1. Create and activate a virtual environment"
    echo "2. Install dependencies: pip install -r requirements.txt"
    exit 1
fi 