import curses
import subprocess

formats = [
    ("140", "m4a   audio only 129k mp4a.40.2"),
    ("251", "webm  audio only 128k opus"),
    ("160", "mp4   144p 30fps 87k avc1"),
    ("134", "mp4   360p 30fps 421k avc1"),
    ("18",  "mp4   360p 30fps 468k avc1 + mp4a"),
    ("243", "webm  360p 30fps 338k vp9"),
    ("136", "mp4   720p 30fps 1405k avc1"),
    ("298", "mp4   720p60 1836k avc1"),
    ("299", "mp4   1080p60 3380k avc1"),
]

def menu(stdscr):
    curses.curs_set(0)
    selected = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "🎬 Select a format using ↑ ↓ and press Enter:\n", curses.A_BOLD)

        for i, (fmt_id, desc) in enumerate(formats):
            if i == selected:
                stdscr.addstr(i + 2, 2, f"> {fmt_id} — {desc}", curses.A_REVERSE)
            else:
                stdscr.addstr(i + 2, 2, f"  {fmt_id} — {desc}")

        key = stdscr.getch()
        if key == curses.KEY_UP and selected > 0:
            selected -= 1
        elif key == curses.KEY_DOWN and selected < len(formats) - 1:
            selected += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            return formats[selected][0]

def confirm_download():
    while True:
        choice = input("📥 Do you want to download this format? (y/n): ").strip().lower()
        if choice in ["y", "n"]:
            return choice == "y"

def main():
    url = input("🔗 Enter YouTube URL: ").strip()
    selected_format = curses.wrapper(menu)
    print(f"\n✅ You selected format: {selected_format}")

    if confirm_download():
        print(f"\n▶ Running: python -m yt_dlp -f {selected_format} \"{url}\"")
        subprocess.run(["python", "-m", "yt_dlp", "-f", selected_format, url])
        print("🎉 Download complete.")
    else:
        print("❌ Download canceled.")

if __name__ == "__main__":
    main()