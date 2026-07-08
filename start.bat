@echo off
title Webull Trading Bot Launcher
setlocal enabledelayedexpansion
set PYTHONUTF8=1

rem Adjust console size and theme color
mode con: cols=90 lines=26
color 0B

echo =================================================================================
echo                   WEBULL TRADING BOT SYSTEMS LAUNCH CONTROLLER
echo =================================================================================
echo.

rem 1. Pre-flight Checks
echo [*] Running System Pre-flight Checks...

rem Check Port 8484 (FastAPI Backend)
netstat -aon | findstr :8484 | findstr LISTENING >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo [ERROR] Port 8484 is already in use by another process!
    echo         Please run 'stop.bat' first to clean up old instances.
    echo.
    pause
    exit /b 1
)

rem Check Port 4018 (Next.js Frontend)
netstat -aon | findstr :4018 | findstr LISTENING >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo [ERROR] Port 4018 is already in use by another process!
    echo         Please run 'stop.bat' first to clean up old instances.
    echo.
    pause
    exit /b 1
)

echo [OK] System checks passed. Ports 8484 and 4018 are free.
echo ---------------------------------------------------------------------------------
echo.

rem 2. Launch Services (minimizing spawned cmd windows to avoid screen clutter)
echo [*] Launching Python FastAPI Backend Server...
start "Webull API Backend" /min cmd /c "python server.py"
timeout /t 2 >nul
echo [OK] Backend successfully initialized.
echo.

echo [*] Launching Next.js Frontend Web Dashboard...
start "Webull Web Dashboard" /min cmd /c "cd frontend && npx next dev -p 4018"
timeout /t 3 >nul
echo [OK] Frontend successfully initialized.
echo ---------------------------------------------------------------------------------
echo.
echo  Webull Trading Bot services are now running!
echo.
echo   - Python API Server  : http://127.0.0.1:8484
echo   - Web User Interface : http://localhost:4018
echo.
echo ---------------------------------------------------------------------------------
echo  [IMPORTANT] Keep this controller window open while using the bot.
echo  [IMPORTANT] To stop all services cleanly, run 'stop.bat' or close this window.
echo ---------------------------------------------------------------------------------
echo.
pause
