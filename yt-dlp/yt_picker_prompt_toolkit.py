import subprocess
import re
import urllib.parse
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.styles import Style

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
    print(f"\n🔍 Fetching formats for: {url}\n")
    result = subprocess.run(["python", "-m", "yt_dlp", "-F", url], capture_output=True, text=True)
    print(result.stdout)

    lines = result.stdout.splitlines()
    formats = []

    for line in lines:
        if not re.match(r"^\d{2,3}\s", line):
            continue
        parts = re.split(r"\s{2,}", line.strip())
        if len(parts) < 2:
            continue
        fmt_id = parts[0].split()[0]
        desc = "  ".join(parts[1:])
        formats.append((fmt_id, desc))

    return formats

# --- Prompt for format selection ---
def select_format(formats):
    choices = [(fmt_id, f"{fmt_id} — {desc}") for fmt_id, desc in formats]
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
        cancel_text="Cancel"
    ).run()

    return result

# --- Confirm and run download ---
def confirm_download(fmt_id, url):
    choice = prompt(f"\n📥 Download format {fmt_id}? (Enter for yes, n to cancel): ").strip().lower()
    if choice in ["", "y", "yes"]:
        print(f"\n▶ Running: yt_dlp -f {fmt_id} \"{url}\"")
        subprocess.run(["python", "-m", "yt_dlp", "-f", fmt_id, url])
        print("🎉 Download complete.")
    else:
        print("❌ Download canceled.")

# --- Main flow ---
def main():
    raw_url = prompt("🔗 Enter YouTube URL: ").strip()
    url = clean_url(raw_url)
    formats = fetch_formats(url)
    if not formats:
        print("⚠️ No formats found.")
        return

    selected_format = select_format(formats)
    if selected_format:
        confirm_download(selected_format, url)
    else:
        print("❌ No format selected.")

if __name__ == "__main__":
    main()