@echo off
REM ============================================
REM ESH.TRADE - ULTIMATE start.bat
REM Complete Production & Development Script
REM ============================================

setlocal enabledelayedexpansion

REM ============ COLORS ============
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "RESET=[0m"

REM ============ HEADER ============
echo %BLUE%========================================%RESET%
echo %GREEN%🚀 ESH.TRADE - ULTIMATE TRADING PLATFORM%RESET%
echo %BLUE%========================================%RESET%
echo.

REM ============ CHECK PYTHON ============
echo %BLUE%📍 Checking Python...%RESET%

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo %RED%❌ Python not found. Please install Python 3.9+%RESET%
    echo %BLUE%Download: https://python.org/downloads%RESET%
    pause
    exit /b 1
)

python --version
echo %GREEN%✅ Python found%RESET%
echo.

REM ============ CHECK PIP ============
echo %BLUE%📍 Checking pip...%RESET%

where pip >nul 2>nul
if %errorlevel% neq 0 (
    echo %RED%❌ pip not found%RESET%
    pause
    exit /b 1
)

echo %GREEN%✅ pip found%RESET%
echo.

REM ============ CREATE VENV ============
echo %BLUE%📍 Setting up virtual environment...%RESET%

if not exist "venv" (
    echo %YELLOW%ℹ️  Creating virtual environment...%RESET%
    python -m venv venv
    echo %GREEN%✅ Virtual environment created%RESET%
) else (
    echo %GREEN%✅ Virtual environment already exists%RESET%
)

call venv\Scripts\activate.bat
echo %GREEN%✅ Virtual environment activated%RESET%
echo.

REM ============ INSTALL DEPENDENCIES ============
echo %BLUE%📍 Installing dependencies...%RESET%

if not exist "venv\.installed" (
    echo %YELLOW%ℹ️  Upgrading pip...%RESET%
    python -m pip install --upgrade pip -q
    
    echo %YELLOW%ℹ️  Installing requirements...%RESET%
    pip install -r requirements.txt -q
    
    echo. > venv\.installed
    echo %GREEN%✅ Dependencies installed%RESET%
) else (
    echo %GREEN%✅ Dependencies already installed%RESET%
)
echo.

REM ============ CHECK .env ============
echo %BLUE%📍 Checking environment file...%RESET%

if not exist ".env" (
    echo %YELLOW%⚠️  .env file not found%RESET%
    echo %RED%❌ Please create .env file%RESET%
    pause
    exit /b 1
) else (
    echo %GREEN%✅ .env file found%RESET%
)
echo.

REM ============ CREATE DIRECTORIES ============
echo %BLUE%📍 Creating directories...%RESET%

if not exist "data\logs" mkdir data\logs
if not exist "data\backups" mkdir data\backups
if not exist "data\cache" mkdir data\cache
if not exist "data\sessions" mkdir data\sessions
if not exist "data\biometric" mkdir data\biometric
if not exist "data\temp" mkdir data\temp

echo %GREEN%✅ Directories created%RESET%
echo.

REM ============ CHECK DATABASE ============
echo %BLUE%📍 Checking database...%RESET%

if not exist "data\estrade.db" (
    echo %YELLOW%ℹ️  Initializing database...%RESET%
    python -c "from backend.app.database import DatabaseManager; db = DatabaseManager(); print('✅ Database initialized')" 2>nul
) else (
    echo %GREEN%✅ Database exists%RESET%
)
echo.

REM ============ CHECK EMAIL ============
echo %BLUE%📍 Checking email configuration...%RESET%

findstr /C:"GMAIL_APP_PASSWORD=" .env >nul 2>nul
if %errorlevel% neq 0 (
    echo %YELLOW%⚠️  Email not configured (TOTP will work without email)%RESET%
) else (
    echo %GREEN%✅ Email configured%RESET%
)
echo.

REM ============ PRE-START CHECKS ============
echo %BLUE%📍 Running pre-start checks...%RESET%

python -c "from backend.app.config import settings; print(f'✅ {settings.APP_NAME} v{settings.APP_VERSION}')" 2>nul
echo.

REM ============ START APPLICATION ============
echo %BLUE%========================================%RESET%
echo %GREEN%🚀 Starting ESH.TRADE...%RESET%
echo %BLUE%========================================%RESET%
echo.
echo %GREEN%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo   🌐 URL:      http://localhost:8000
echo   📚 Docs:     http://localhost:8000/api/docs
echo   🔑 Admin:    admin123 / eSmwas@2004
echo   📧 Email:    estradingmachine@gmail.com
echo %GREEN%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo.

REM Check mode
if "%1"=="--reload" (
    echo %YELLOW%ℹ️  Development mode with hot reload%RESET%
    python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
) else if "%1"=="--dev" (
    echo %YELLOW%ℹ️  Development mode%RESET%
    python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 1 --reload --log-level debug
) else if "%1"=="--prod" (
    echo %YELLOW%ℹ️  Production mode%RESET%
    python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 8 --log-level info
) else (
    echo %YELLOW%ℹ️  Standard mode%RESET%
    python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
)

pause