@echo off
title 0 Piso Cash Card System - Automated Setup
echo Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed! 
    echo Please install Python from https://www.python.org/ and check "Add to PATH".
    pause
    exit
)

echo Checking and installing dependencies...

:: Check for Flask
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Flask...
    pip install flask
) else (
    echo Flask is already installed.
)

:: Check for Pytz (Timezone Support)
python -c "import pytz" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Pytz...
    pip install pytz
) else (
    echo Pytz is already installed.
)

echo.
echo Starting 0 Piso System...
:: Runs the Flask app in the background
start /b python app.py

echo Waiting 5 seconds for the server to wake up...
timeout /t 5 /nobreak >nul

:: Open the default browser
start http://127.0.0.1:5000

echo.
echo ==============================================
echo SYSTEM IS ONLINE
echo Please keep this window open while in use.
echo ==============================================
echo.
pause