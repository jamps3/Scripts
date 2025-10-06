![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)
![License](https://img.shields.io/badge/License-MIT-green?logo=open-source-initiative)
![Build](https://img.shields.io/badge/Build-Stable-brightgreen?logo=check-circle)

<img src="https://github.com/jamps3/Scripts/blob/master/sleep_timer/feather.png" alt="Feather Icon" width="100"></img>
# Windows sleep timer utility with GUI

User-friendly sleep timer for Windows. Choose your delay, watch the countdown, and drift into sleep—with a feather-light touch.

---

## 🖥️ Features

- ⏱️ Live countdown with minute:second display
- ❌ Abort anytime with a single key or button
- 🖱️ GUI with dropdowns and custom time entry
- 💤 Puts your system to sleep using native Windows calls
- 🌅 Displays how long you slept when you return

---

## 🚀 How to Use

### CLI
```bash
python sleep_timer.py 30
```

### GUI
```bash
python sleep_timer_gui.py
```

## Latest release: [sleep_timer_gui.exe](https://github.com/jamps3/Scripts/blob/master/sleep_timer/dist/sleep_timer_gui.exe)

![screenshot](https://github.com/jamps3/Scripts/blob/master/sleep_timer/screenshot.png)

## Development

### Create .exe
```bash
pyinstaller --onefile --windowed --icon=feather.ico sleep_timer_gui.py
```

## Assets
- feather.png – icon used in GUI and .exe
- feather.ico – converted icon for Windows executable

## Future Ideas
- Tray icon with countdown tooltip
- Sound cues before sleep
- Cross-platform support (Linux/macOS)
- Splash screen with animated feather
