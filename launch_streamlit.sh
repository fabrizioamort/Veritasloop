#!/bin/bash
# Launch VeritasLoop Streamlit Web Interface
# This script starts the Streamlit web application

echo "========================================"
echo " VeritasLoop - Web Interface Launcher"
echo "========================================"
echo ""
echo "Starting Streamlit application..."
echo "The web interface will open in your browser at:"
echo "  http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

# Activate virtual environment and run streamlit
source .venv/bin/activate
streamlit run app.py
