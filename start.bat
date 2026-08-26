@echo off
echo ============================================
echo   ESMH.TRADE Backend Startup
echo ============================================

cd backend

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create data directory
if not exist ..\data mkdir ..\data
if not exist ..\data\logs mkdir ..\data\logs

REM Start server
echo Starting ESMH.TRADE API...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
