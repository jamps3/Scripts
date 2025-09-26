@echo off
setlocal enabledelayedexpansion

:: Check if URL is provided
set "URL=%~1"
:: Handle URLs with special characters
if "%URL:~0,4%"=="http" (
    set "URL=%URL:&=^&%"
)

:: Set quality parameter (can be 2nd or 3rd argument)
set "QUALITY=4K"
set "QUALITY_ARG2=0"
if not "%~2"=="" (
    if /i "%~2"=="8K" (set "QUALITY=8K" && set "QUALITY_ARG2=1")
    if /i "%~2"=="4K" (set "QUALITY=4K" && set "QUALITY_ARG2=1")
    if /i "%~2"=="FHD" (set "QUALITY=FHD" && set "QUALITY_ARG2=1")
    if /i "%~2"=="HD" (set "QUALITY=HD" && set "QUALITY_ARG2=1")
)
if not "%~3"=="" (
    if /i "%~3"=="8K" set "QUALITY=8K"
    if /i "%~3"=="4K" set "QUALITY=4K"
    if /i "%~3"=="FHD" set "QUALITY=FHD"
    if /i "%~3"=="HD" set "QUALITY=HD"
)

:: Set format based on quality
if /i "!QUALITY!"=="8K" set "FORMAT=bestvideo[height<=4320]+bestaudio/best"
if /i "!QUALITY!"=="4K" set "FORMAT=bestvideo[height<=2160]+bestaudio/best"
if /i "!QUALITY!"=="FHD" set "FORMAT=bestvideo[height<=1080]+bestaudio/best"
if /i "!QUALITY!"=="HD" set "FORMAT=bestvideo[height<=720]+bestaudio/best"

:: Check if we have a directory path (not a quality option)
set "IS_DOWNLOAD=0"
if not "%~2"=="" (
    if not "%~2"=="." (
        if "!QUALITY_ARG2!"=="0" (
            set "IS_DOWNLOAD=1"
            set "DEST_DIR=%~2"
        )
    )
)

:: Escape ampersands in URL
set "URL=%URL:&=^&%"

if "!IS_DOWNLOAD!"=="1" (
    echo Downloading !QUALITY! video to: "!DEST_DIR!"
    echo Running: python -m yt_dlp --no-playlist -f "!FORMAT!" -o "!DEST_DIR!\%%(title)s.%%(ext)s" "!URL!"
    
    cmd /c ""python" -m yt_dlp --no-playlist -f "!FORMAT!" -o "!DEST_DIR!\%%(title)s.%%(ext)s" "!URL!""
    
    echo Done downloading.
) else (
    echo Streaming !QUALITY! video in VLC...
    echo Running: python -m yt_dlp --no-playlist -f "!FORMAT!" -o "!DEST_DIR!\%%(title)s.%%(ext)s" "!URL!" | vlc -
    
    "python" -m yt_dlp --no-playlist -f "!FORMAT!" -o - "!URL!" | vlc -
)

endlocal
