@echo off
title Crypto Signal System Launcher
cd /d %~dp0

:menu
cls
echo -------------------------------------
echo   CRYPTO SIGNAL SYSTEM - MAIN MENU
echo -------------------------------------
echo 1. Run Real-Time WebSocket Signals
echo 2. Run Flask Dashboard
echo 3. Run Backtester
echo 4. Exit
echo -------------------------------------
set /p choice="Enter your choice: "

if "%choice%"=="1" goto websocket
if "%choice%"=="2" goto flask
if "%choice%"=="3" goto backtest
if "%choice%"=="4" exit

:websocket
echo Launching Real-Time WebSocket...
python my_modules\websocket_client_real_time.py
pause
goto menu

:flask
echo Launching Flask Dashboard...
python flask_app.py
pause
goto menu

:backtest
echo Running Backtester...
python my_modules\backtester.py
pause
goto menu
