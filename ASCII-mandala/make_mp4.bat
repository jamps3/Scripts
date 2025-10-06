@echo off
REM Create MP4 animation from frames folder

REM Default values
set FRAMERATE=60
set OUTPUT_FILE=animation.mp4

REM Use command line parameters if given
if not "%~1"=="" set OUTPUT_FILE=%~1
if not "%~2"=="" set FRAMERATE=%~2

REM frames folder of project directory
set "FRAMES_DIR=%~dp0frames"

REM Execute FFmpeg with cmd so PowerShell doesn't mess up the variables
cmd /c ffmpeg -framerate %FRAMERATE% -i "%FRAMES_DIR%\frame_%%04d.png" -c:v libx264 -pix_fmt yuv420p "%~dp0%OUTPUT_FILE%"

echo Animation created: %OUTPUT_FILE% @ %FRAMERATE%fps
