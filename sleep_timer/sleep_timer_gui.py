import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import subprocess

class SleepTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sleep Timer")
        self.root.geometry("300x300")
        self.abort_flag = False

        self.label = ttk.Label(root, text="Select sleep delay:")
        self.label.pack(pady=10)

        self.options = [15, 30, 45, 60, 75, 90, 105, 120]
        self.selected = tk.IntVar(value=self.options[0])
        self.dropdown = ttk.Combobox(root, textvariable=self.selected, values=self.options, state="readonly")
        self.dropdown.pack()

        self.custom_label = ttk.Label(root, text="Or enter custom time (min):")
        self.custom_label.pack(pady=5)
        self.custom_entry = ttk.Entry(root)
        self.custom_entry.pack()

        self.start_button = ttk.Button(root, text="Start Countdown", command=self.start_countdown)
        self.start_button.pack(pady=10)

        self.abort_button = ttk.Button(root, text="Abort", command=self.abort_countdown, state="disabled")
        self.abort_button.pack()

        self.status = ttk.Label(root, text="")
        self.status.pack(pady=5)

    def start_countdown(self):
        try:
            minutes = float(self.custom_entry.get()) if self.custom_entry.get() else self.selected.get()
            if minutes <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter a positive number.")
            return

        self.abort_flag = False
        self.abort_button.config(state="normal")
        self.start_button.config(state="disabled")
        self.status.config(text=f"Countdown started: {minutes:.1f} min")

        threading.Thread(target=self.run_countdown, args=(minutes,), daemon=True).start()

    def abort_countdown(self):
        self.abort_flag = True
        self.status.config(text="❌ Countdown aborted.")
        self.abort_button.config(state="disabled")
        self.start_button.config(state="normal")

    def run_countdown(self, minutes):
        total_seconds = int(minutes * 60)
        for remaining in range(total_seconds, 0, -1):
            if self.abort_flag:
                return
            mins, secs = divmod(remaining, 60)
            self.status.config(text=f"🕒 Time left: {mins:02d}:{secs:02d}")
            time.sleep(1)

        self.status.config(text="💤 Sleeping now...")
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])

if __name__ == "__main__":
    root = tk.Tk()
    app = SleepTimerApp(root)
    root.mainloop()