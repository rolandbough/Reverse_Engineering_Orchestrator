@echo off
REM Windows batch script for automated commits
REM Can be scheduled using Windows Task Scheduler

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    exit /b 1
)

REM Run the automation script
python version_manager.py --auto

REM Log the execution
echo [%date% %time%] Automation script executed >> automation.log

