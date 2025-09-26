import curses
import subprocess
import re
import urllib.parse
import locale
import sys
import os
os.environ["PYTHONIOENCODING"] = "utf-8"

locale.setlocale(locale.LC_ALL, '')  # Help curses handle Unicode

def clean_url(url):
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    video_id = query.get("v", [""])[0]
    if not video_id:
        return url
    return f"https://www.youtube.com/watch?v={video_id}"

def fetch_formats(url):
    print(f"\n🔍 Fetching formats for: {url}\n")
    result = subprocess.run(["python", "-m", "yt_dlp", "-F", url], capture_output=True, text=True)
    print(result.stdout)  # Show full output before menu

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

def menu(stdscr, formats):
    curses.curs_set(0)
    selected = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "🎬 Select a format using ↑ ↓ and press Enter:\n", curses.A_BOLD)

        for i, (fmt_id, desc) in enumerate(formats):
            line = f"{fmt_id} — {desc}"
            if i == selected:
                stdscr.addstr(i + 2, 2, f"> {line}", curses.A_REVERSE)
            else:
                stdscr.addstr(i + 2, 2, f"  {line}")

        key = stdscr.getch()
        if key == curses.KEY_UP and selected > 0:
            selected -= 1
        elif key == curses.KEY_DOWN and selected < len(formats) - 1:
            selected += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            return formats[selected][0]

def confirm_download(fmt_id, url):
    print(f"\n📥 Download format {fmt_id}? (Y/n): ", end="", flush=True)
    choice = input().strip().lower()
    if choice in ["y", "yes", ""]:
        print(f"\n▶ Running: yt_dlp -f {fmt_id} \"{url}\"")
        subprocess.run(["python", "-m", "yt_dlp", "-f", fmt_id, url])
        print("🎉 Download complete.")
    else:
        print("❌ Download canceled.")

def main():
    raw_url = input("🔗 Enter YouTube URL: ").strip()
    url = clean_url(raw_url)
    formats = fetch_formats(url)
    if not formats:
        print("⚠️ No formats found.")
        return

    try:
        selected_format = curses.wrapper(lambda stdscr: menu(stdscr, formats))
    except Exception as e:
        print(f"⚠️ Menu error: {e}")
        sys.exit(1)

    confirm_download(selected_format, url)

if __name__ == "__main__":
    main()
