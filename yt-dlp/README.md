# yt-dlp Scripts

This directory contains scripts and utilities for working with [yt-dlp](https://github.com/yt-dlp/yt-dlp), a command-line program to download videos from YouTube and other sites.

## Contents

- Scripts for automating yt-dlp tasks
- Configuration examples for common use cases

## Details

### dl.py: Simple Python YouTube downloader with destination directory and quality parameters
### dl.cmd: Simple Windows CMD version
### ytdl.py: Python yt-dlp downloader with a menu interface to select the format(s)

## Usage

1. Ensure [yt-dlp](https://github.com/yt-dlp/yt-dlp) is installed. The ytdl.py script checks for required dependencies and installs yt-dlp if not found.
2. Run the script:

```bash
python ytdl.py
```

3. Screenshots

![ytdl.py screenshot](https://github.com/jamps3/Scripts/blob/master/yt-dlp/ytdl.png)
![ytdl.py screenshot 2](https://github.com/jamps3/Scripts/blob/master/yt-dlp/ytdl_2.png)

# Streaming YouTube in VLC

## Forcing 4K resolution playback in VLC

To force 4K resolution playback in VLC from YouTube, you need to use either:

✅ Option 1: Use yt-dlp to fetch the direct 4K stream and open it in VLC

This is the most reliable method.

🔧 Step-by-step:

    Install yt-dlp (if you haven’t):

2.  pip install -U yt-dlp

    Find the best 4K video stream URL and launch VLC:

3.  yt-dlp -f "bestvideo[height=2160]+bestaudio/best[height=2160]" -g "https://www.youtube.com/watch?v=VIDEO_ID"

        This returns a direct stream URL (or two: video + audio).
        Copy and paste the full stream URL into VLC:
            Open VLC → Media → Open Network Stream → paste the URL → Play.

🔁 One-liner (Linux/macOS/WSL/Powershell):

vlc "$(yt-dlp -f 'bestvideo[height=2160]+bestaudio/best[height=2160]' -g 'https://www.youtube.com/watch?v=VIDEO_ID')"

📝 Notes:

    Replace VIDEO_ID with your desired YouTube video ID.
    This ensures VLC directly streams 4K, skipping YouTube’s adaptive logic.

✅ Bonus Tip (Download instead):

If you’d rather download the 4K video:

yt-dlp -f "bestvideo[height=2160]+bestaudio/best" -o "%(title)s.%(ext)s" "https://www.youtube.com/watch?v=VIDEO_ID"
