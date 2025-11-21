@echo off
echo ========================================
echo   Sales Analytics Dashboard Launcher
echo ========================================
echo.
echo Starting dashboard server...
echo.
cd /d "%~dp0"
python app.py
pause
