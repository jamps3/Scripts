@echo off
setlocal enabledelayedexpansion

REM Dynamically set ADB path based on current user
set ADB="C:\Users\%USERNAME%\AppData\Local\Android\Sdk\platform-tools\adb.exe"

REM Set log file path
set LOGFILE=adb_tether_log.txt

REM Clear log file
echo. > %LOGFILE%

echo Starting USB tethering monitor... >> %LOGFILE%
echo [%DATE% %TIME%] Starting USB tethering monitor...

:loop
echo [%DATE% %TIME%] Checking for devices... >> %LOGFILE%
%ADB% devices >> %LOGFILE%
echo. >> %LOGFILE%

REM Check for authorized devices
%ADB% devices | findstr "device$" >nul
set AUTHORIZED=%errorlevel%

REM Check for unauthorized devices
%ADB% devices | findstr "unauthorized" >nul
set UNAUTHORIZED=%errorlevel%

if %AUTHORIZED%==0 (
    echo [%DATE% %TIME%] Authorized device detected. >> %LOGFILE%
    echo Configuring USB tethering... >> %LOGFILE%
    %ADB% shell svc usb setFunctions none >> %LOGFILE%
    timeout /t 2 >nul
    %ADB% shell svc usb setFunctions rndis >> %LOGFILE%
    echo [%DATE% %TIME%] USB tethering enabled. Waiting for disconnect... >> %LOGFILE%

    :waitdisconnect
    timeout /t 5 >nul
    %ADB% get-state >nul 2>&1
    if %errorlevel%==0 goto waitdisconnect
    echo [%DATE% %TIME%] Device disconnected. Waiting for reconnect... >> %LOGFILE%

) else if %UNAUTHORIZED%==0 (
    echo [%DATE% %TIME%] Only unauthorized devices detected. Sleeping for 30 seconds... >> %LOGFILE%
    timeout /t 30 >nul
) else (
    echo [%DATE% %TIME%] No devices found. Waiting... >> %LOGFILE%
    timeout /t 3 >nul
)

goto loop