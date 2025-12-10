
@echo off
echo Starting VeritasLoop Intelligence Hub...

echo Starting Backend API...
start "VeritasLoop Backend" cmd /k "uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"

echo Starting Frontend Interface...
cd frontend
npm run dev
