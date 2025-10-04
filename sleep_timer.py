import time
import subprocess
import argparse
import sys
import threading
import msvcrt  # Windows-only for keyboard input

def sleep_after_delay(minutes):
    seconds = int(minutes * 60)
    print(f"\n⏳ Countdown started: {minutes} minute(s) until sleep.")
    print("Press Q to abort.\n")

    aborted = False

    def check_for_abort():
        nonlocal aborted
        while not aborted:
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8').lower()
                if key == 'q':
                    aborted = True
                    print("\n❌ Sleep aborted by user.")
                    break

    abort_thread = threading.Thread(target=check_for_abort, daemon=True)
    abort_thread.start()

    for remaining in range(seconds, 0, -1):
        if aborted:
            return
        mins, secs = divmod(remaining, 60)
        print(f"\r🕒 Time left: {mins:02d}:{secs:02d}", end="")
        time.sleep(1)

    print("\n💤 Putting system to sleep now...")
    subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])

def interactive_menu():
    print("\n🛌 Sleep Timer Menu")
    print("Choose a delay before sleep:")
    options = [15, 30, 45, 60, 75, 90, 105, 120]
    for i, val in enumerate(options, start=1):
        print(f"  {i}. {val} minutes")
    print("  C. Custom time")
    print("  Q. Quit")

    choice = input("\nEnter your choice (1–8, C, or Q): ").strip().lower()

    if choice == 'q':
        print("👋 Exiting without setting a sleep timer.")
        sys.exit(0)
    elif choice == 'c':
        try:
            custom = float(input("Enter custom time in minutes: "))
            if custom <= 0:
                print("❌ Time must be positive. Exiting.")
                sys.exit(1)
            return custom
        except ValueError:
            print("❌ Invalid input. Exiting.")
            sys.exit(1)
    else:
        try:
            index = int(choice)
            if 1 <= index <= len(options):
                return options[index - 1]
            else:
                print("❌ Invalid choice. Exiting.")
                sys.exit(1)
        except ValueError:
            print("❌ Invalid input. Exiting.")
            sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Put Windows to sleep after a delay.")
    parser.add_argument("minutes", type=float, nargs="?", help="Delay time in minutes before sleep")
    args = parser.parse_args()

    if args.minutes is not None:
        sleep_after_delay(args.minutes)
    else:
        selected = interactive_menu()
        sleep_after_delay(selected)