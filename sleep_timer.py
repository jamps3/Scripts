import time
import subprocess
import argparse
import sys

def sleep_after_delay(minutes):
    seconds = int(minutes * 60)
    print(f"\n⏳ Waiting {minutes} minute(s) before sleeping...")
    time.sleep(seconds)
    subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])

def interactive_menu():
    print("\n🛌 Sleep Timer Menu")
    print("Choose a delay before sleep:")
    options = [15, 30, 45, 60, 75, 90, 105, 120]
    for i, val in enumerate(options, start=1):
        print(f"  {i}. {val} minutes")
    try:
        choice = int(input("\nEnter your choice (1–8): "))
        if 1 <= choice <= len(options):
            return options[choice - 1]
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