import subprocess
import re
import urllib.parse
import time
import sys
import platform
import shutil
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# List of required libraries for all platforms
required_libraries = [
    ("prompt_toolkit", "prompt_toolkit"),
    ("yt_dlp", "yt_dlp"),
    ("yt_dlp_ejs", "yt-dlp-ejs"),
]

# --- Install missing libraries ---
def install_missing_libraries():
    # Install common libraries
    for import_name, package_name in required_libraries:
        try:
            __import__(import_name)
        except ImportError:
            print(f"⚠️ Missing library: {package_name}. Installing now...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

    # Check the platform and install platform-specific libraries
    if platform.system() == "Windows":
        # Install windows-curses for Windows
        try:
            __import__("curses")
        except ImportError:
            print("⚠️ Missing 'curses' library on Windows. Installing 'windows-curses'...")
            subprocess.check_call([subprocess.sys.executable, "-m", "pip", "install", "windows-curses"])

    elif platform.system() == "Linux":
        try:
            __import__("curses")
        except ImportError:
            print("⚠️ Missing 'curses' library on Linux. Installing necessary libraries...")
            subprocess.check_call([subprocess.sys.executable, "-m", "pip", "install", "curses"])

def find_ffmpeg_location():
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return str(Path(ffmpeg_path).parent)

    winget_packages = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    matches = sorted(winget_packages.glob("Gyan.FFmpeg_*/*/bin/ffmpeg.exe"), reverse=True)
    if matches:
        return str(matches[0].parent)

    return None

def build_ytdlp_cmd():
    cmd = ["python", "-m", "yt_dlp", "--js-runtimes", "node"]
    ffmpeg_location = find_ffmpeg_location()
    if ffmpeg_location:
        cmd.extend(["--ffmpeg-location", ffmpeg_location])
    return cmd

def load_prompt_toolkit():
    from prompt_toolkit import prompt
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.shortcuts import radiolist_dialog
    from prompt_toolkit.styles import Style

    return prompt, HTML, radiolist_dialog, Style

# --- Clean YouTube URL ---
def clean_url(url):
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    video_id = query.get("v", [""])[0]
    if not video_id:
        return url
    return f"https://www.youtube.com/watch?v={video_id}"

# --- Fetch formats from yt_dlp ---
def fetch_formats(url):
    _, HTML, _, _ = load_prompt_toolkit()
    print(f"\n🔍 Fetching formats for: {url}\n")
    result = subprocess.run([*build_ytdlp_cmd(), "-F", url], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    lines = result.stdout.splitlines()
    formats = []
    audio_only = []
    video_only = []
    progressive = []

    for line in lines:
        if not re.match(r"^\d+\s", line):
            continue
        parts = re.split(r"\s{2,}", line.strip())
        if len(parts) < 2:
            continue

        fmt_id = parts[0].split()[0]
        desc = "  ".join(parts[1:])
        color = "ansibrightwhite"

        if "audio only" in desc.lower():
            color = "ansiblue"
            audio_only.append((fmt_id, desc))
        elif "video only" in desc.lower():
            color = "ansigreen"
            video_only.append((fmt_id, desc))
        else:
            progressive.append((fmt_id, desc))

        size_match = re.search(r"(\d+(\.\d+)?[KM]iB)", desc)
        bitrate_match = re.search(r"(\d{2,4}k)", desc)
        tooltip = f"{size_match.group(1) if size_match else ''} @ {bitrate_match.group(1) if bitrate_match else ''}"

        label = HTML(f"<{color}>{fmt_id} — {desc}</{color}>")
        formats.append((fmt_id, label, tooltip))

    return formats, audio_only, video_only, progressive

# --- Prompt for format selection ---
def select_format(formats, default_id=None):
    _, _, radiolist_dialog, Style = load_prompt_toolkit()
    choices = [(fmt_id, label) for fmt_id, label, _ in formats]
    tooltips = {fmt_id: tip for fmt_id, _, tip in formats}

    style = Style.from_dict({
        "dialog": "bg:#1e1e1e",
        "dialog.body": "bg:#1e1e1e #ffffff",
        "dialog frame.label": "bg:#1e1e1e #00ffff",
        "dialog.body text-area": "#ffffff",
        "dialog shadow": "bg:#000000",
    })

    result = radiolist_dialog(
        title="🎬 Format Picker",
        text="Select a format to download:",
        values=choices,
        style=style,
        ok_text="Download",
        cancel_text="Cancel",
        default=default_id,  # Auto-select best format
    ).run()

    if result:
        print(f"\n💡 Selected format: {result} — {tooltips.get(result, '')}")
    return result

def wants_flac_conversion():
    prompt, _, _, _ = load_prompt_toolkit()
    choice = prompt("\n🎼 Convert audio to FLAC? (y to convert, Enter to keep original): ").strip().lower()
    return choice in ["y", "yes"]

# --- Confirm and run download ---
def confirm_download(fmt_id, url, postprocess_args=None):
    prompt, _, _, _ = load_prompt_toolkit()
    choice = prompt(f"\n📥 Download format {fmt_id}? (Enter for yes, n to cancel): ").strip().lower()
    if choice in ["", "y", "yes"]:
        cmd = [*build_ytdlp_cmd(), "-f", fmt_id]
        if postprocess_args:
            cmd.extend(postprocess_args)
        cmd.append(url)
        print(f"\n▶ Running: {' '.join(cmd)}")
        subprocess.run(cmd)
        shimmer_badge("🎉 Download complete!")
    else:
        print("❌ Download canceled.")

# --- Shimmer badge animation ---
def shimmer_badge(message):
    gradient = ["#ff5f5f", "#ffaf5f", "#ffff5f", "#afff5f", "#5fff5f", "#5fffaf", "#5fffff", "#5fafff", "#5f5fff"]
    for i in range(3):
        for color in gradient + gradient[::-1]:
            print(f"\r\033[38;2;{int(color[1:3],16)};{int(color[3:5],16)};{int(color[5:],16)}m{message}\033[0m", end="")
            time.sleep(0.05)
    print(f"\r{message}")

# Find best video-only format by bitrate
def extract_bitrate(desc):
    match = re.search(r"(\d{2,4})k", desc)
    return int(match.group(1)) if match else 0

# --- Main flow ---
def main():
    prompt, _, _, _ = load_prompt_toolkit()
    raw_url = prompt("🔗 Enter YouTube URL: ").strip()
    url = clean_url(raw_url)
    formats, audio_only, video_only, progressive = fetch_formats(url)
    if not formats:
        print("⚠️ No formats found.")
        return
    # Auto-select best video format
    best_video_id = None
    if video_only:
        best_video_id = max(video_only, key=lambda x: extract_bitrate(x[1]))[0]

    selected_format = select_format(formats, default_id=best_video_id)
    if not selected_format:
        print("❌ No format selected.")
        return

    # Check if selected is video-only
    if any(fmt_id == selected_format for fmt_id, _ in video_only):
        # Pick best audio (highest bitrate)
        best_audio = max(audio_only, key=lambda x: int(re.search(r"(\d{2,4})k", x[1]).group(1)))
        combo = f"{selected_format}+{best_audio[0]}"
        print(f"\n🎥 Selected video-only format. Auto-merging with best audio: {best_audio[0]}")
        confirm_download(combo, url)

    # If progressive (audio+video), download directly
    elif any(fmt_id == selected_format for fmt_id, _ in progressive):
        print("\n🎬 Selected progressive format with audio+video.")
        confirm_download(selected_format, url)

    # If audio-only, download directly
    elif any(fmt_id == selected_format for fmt_id, _ in audio_only):
        print("\n🎧 Selected audio-only format.")
        postprocess_args = ["-x", "--audio-format", "flac"] if wants_flac_conversion() else None
        confirm_download(selected_format, url, postprocess_args)

    else:
        print("⚠️ Unknown format type. Downloading as-is.")
        confirm_download(selected_format, url)

if __name__ == "__main__":
    install_missing_libraries()
    main()
