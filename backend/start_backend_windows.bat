@echo off
REM DOCUGRAPH Backend - Windows Service Startup Script
REM This script ensures the backend runs continuously on Windows servers

setlocal enabledelayedexpansion

REM Configuration
set BACKEND_DIR=%~dp0
set PYTHON_EXE=python
set PORT=5000
set WORKERS=4

echo.
echo ================================================
echo DOCUGRAPH Backend - Windows Startup
echo ================================================
echo.

REM Check Python is installed
%PYTHON_EXE% --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and add it to your system PATH
    pause
    exit /b 1
)

echo [OK] Python is installed
echo [OK] Backend directory: %BACKEND_DIR%

REM Install/check dependencies
echo.
echo Checking dependencies...
cd /d "%BACKEND_DIR%"
%PYTHON_EXE% -m pip show gunicorn >nul 2>&1
if errorlevel 1 (
    echo Installing Gunicorn...
    %PYTHON_EXE% -m pip install gunicorn
)

REM Start server with auto-restart
echo.
echo ================================================
echo Starting DOCUGRAPH Backend Server
echo ================================================
echo Port: %PORT%
echo Workers: %WORKERS%
echo.
echo Press CTRL+C to stop
echo.

:restart
%PYTHON_EXE% run_production.py
if errorlevel 1 (
    echo.
    echo Server crashed, restarting in 5 seconds...
    timeout /t 5 /nobreak
    goto restart
)

endlocal
