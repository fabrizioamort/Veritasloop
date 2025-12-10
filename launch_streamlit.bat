@echo off
REM Launch VeritasLoop Streamlit Web Interface
REM This script starts the Streamlit web application

echo ========================================
echo  VeritasLoop - Web Interface Launcher
echo ========================================
echo.
echo Starting Streamlit application...
echo The web interface will open in your browser at:
echo   http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Activate virtual environment and run streamlit
call .venv\Scripts\activate.bat
streamlit run app.py
