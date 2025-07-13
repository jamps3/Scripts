@echo off
echo Checking Python installation...

REM Check if python command exists
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo Python is installed.
    goto :run_script
)

REM Check if python3 command exists
python3 --version >nul 2>&1
if %errorlevel% == 0 (
    echo Python3 is installed.
    set PYTHON_CMD=python3
    goto :run_script
)

REM Neither python nor python3 found, install Python
echo Python is not installed. Installing Python using winget...
winget install python
if %errorlevel% == 0 (
    echo Python installation completed successfully.
    echo Please restart this script or your command prompt for the changes to take effect.
    pause
    exit /b 0
) else (
    echo Failed to install Python using winget.
    echo Please install Python manually from https://python.org
    pause
    exit /b 1
)

:run_script
echo Running SSHHosts.py...
if not defined PYTHON_CMD (
    set PYTHON_CMD=python
)
%PYTHON_CMD% SSHHosts.py
pause
