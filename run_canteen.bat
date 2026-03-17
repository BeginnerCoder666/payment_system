@echo off
:: Check if Flask is installed
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo Flask not found. Installing dependencies...
    pip install flask
)

title 0 Piso Cash Card System
echo Starting 0 Piso Canteen System...

:: Runs the Flask app in a separate background process
start /b python app.py

:: Wait for 4 seconds to let the server initialize
timeout /t 2 /nobreak >nul

:: Open the browser after the delay
start http://127.0.0.1:5000

echo.
echo System is running! 
echo Keep this window open to maintain the connection.
echo.
pause