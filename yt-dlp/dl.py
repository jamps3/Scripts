import sys
import subprocess
import os

# --- Validate input ---
if len(sys.argv) < 2:
    print("Usage: dl.py <URL> [DEST_DIR or QUALITY] [QUALITY]")
    sys.exit(1)

url = sys.argv[1].replace("&", "^&")  # Escape ampersands for shell safety

# --- Default quality ---
quality = "4K"
quality_arg2 = False

# --- Parse arguments ---
arg2 = sys.argv[2] if len(sys.argv) > 2 else ""
arg3 = sys.argv[3] if len(sys.argv) > 3 else ""

valid_qualities = {"8K", "4K", "FHD", "HD"}

if arg2.upper() in valid_qualities:
    quality = arg2.upper()
    quality_arg2 = True
elif arg2 and arg2 != ".":
    dest_dir = arg2

if arg3.upper() in valid_qualities:
    quality = arg3.upper()

# --- Format selection ---
format_map = {
    "8K": "bestvideo[height<=4320]+bestaudio/best",
    "4K": "bestvideo[height<=2160]+bestaudio/best",
    "FHD": "bestvideo[height<=1080]+bestaudio/best",
    "HD": "bestvideo[height<=720]+bestaudio/best"
}
format_str = format_map.get(quality, format_map["4K"])

# --- Determine mode ---
is_download = False
if arg2 and not quality_arg2 and arg2 != ".":
    is_download = True
    dest_dir = arg2

# --- Run yt_dlp ---
if is_download:
    print(f"📥 Downloading {quality} video to: {dest_dir}")
    cmd = [
        "python", "-m", "yt_dlp",
        "--no-playlist",
        "-f", format_str,
        "-o", os.path.join(dest_dir, "%(title)s.%(ext)s"),
        url
    ]
else:
    print(f"📺 Streaming {quality} video in VLC...")
    cmd = f'python -m yt_dlp --no-playlist -f "{format_str}" -o - "{url}" | vlc -'
    subprocess.run(cmd, shell=True)
    sys.exit(0)

# --- Execute ---
print("▶ Running:", " ".join(cmd))
subprocess.run(cmd)
print("✅ Done downloading.")