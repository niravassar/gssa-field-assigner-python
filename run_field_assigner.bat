@echo off
title GSSA Field Assigner Runner
echo Starting GSSA Field Assigner...
echo.

:: Check if python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in your PATH.
    pause
    exit
)

:: Run the script
python field_assigner.py

:: If the script crashes, keep the window open so you can read the error
if %errorlevel% neq 0 (
    echo.
    echo The script encountered an error.
    pause
)