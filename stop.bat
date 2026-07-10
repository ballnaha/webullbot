@echo off
title Webull Trading Bot - Service Stopper
setlocal enabledelayedexpansion

rem Adjust console size and theme color
mode con: cols=80 lines=22
color 0C

echo ================================================================================
echo                  WEBULL TRADING BOT SERVICE TERMINATION UTILITY
echo ================================================================================
echo.
echo [*] Initiating services shutdown sequence...
echo.

rem 1. Stop Python FastAPI Backend (Port 8484) and its process tree
set backend_stopped=0
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8484 ^| findstr LISTENING') do (
    taskkill /f /t /pid %%a >nul 2>&1
    echo [OK] Terminated Backend Service PID %%a running on port 8484
    set backend_stopped=1
)
if !backend_stopped! equ 0 (
    echo [INFO] Backend Service: No active process found on port 8484.
)

echo.

rem 2. Stop Next.js Frontend (Port 4018) and its process tree
set frontend_stopped=0
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :4018 ^| findstr LISTENING') do (
    taskkill /f /t /pid %%a >nul 2>&1
    echo [OK] Terminated Next.js Service PID %%a running on port 4018
    set frontend_stopped=1
)
if !frontend_stopped! equ 0 (
    echo [INFO] Next.js Service: No active process found on port 4018.
)

echo.

rem 3. Close any spawned command prompt windows matching the launcher titles
echo [*] Terminating Spawned Console Windows...
taskkill /f /im cmd.exe /fi "windowtitle eq Webull API Backend*" >nul 2>&1
taskkill /f /im cmd.exe /fi "windowtitle eq Webull Web Dashboard*" >nul 2>&1
taskkill /f /im cmd.exe /fi "windowtitle eq Webull Trading Bot Launcher*" >nul 2>&1
echo [OK] Spawned console windows terminated successfully.

echo.
echo --------------------------------------------------------------------------------
echo [OK] All Webull Bot services have been stopped successfully!
echo [INFO] Closing this window in 2 seconds...
echo --------------------------------------------------------------------------------
echo.
ping -n 3 127.0.0.1 >nul
