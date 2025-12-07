@echo off
REM Quick Start Script for Trend Scout
REM Studio Pixelens - Instagram Viral Content Discovery

echo ============================================================
echo     TREND SCOUT - Quick Start
echo     Studio Pixelens ^| Web Design ^& UI/UX Niche
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.x from https://www.python.org
    pause
    exit /b 1
)

echo [1/4] Checking Python installation...
python --version
echo.

REM Check if dependencies are installed
echo [2/4] Checking dependencies...
python -c "import instaloader" >nul 2>&1
if errorlevel 1 (
    echo Dependencies not found. Installing...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo Dependencies already installed
)
echo.

REM Check for .env file
echo [3/4] Checking configuration...
if not exist .env (
    echo .env file not found. Using default configuration.
    echo You can create .env from .env.example for custom settings.
) else (
    echo .env file found - using custom configuration
)
echo.

REM Run the application in test mode
echo [4/4] Starting Trend Scout in TEST MODE...
echo.
echo ============================================================
echo  Running with limited posts for initial test
echo  This is safe and won't risk rate limits
echo ============================================================
echo.
python main.py --test-mode --limit 5

echo.
echo ============================================================
echo  Trend Scout Test Complete!
echo ============================================================
echo.
echo Next Steps:
echo  1. Check viral_trends.json for results
echo  2. Review trend_scout.log for details
echo  3. For full run: python main.py
echo.
pause
