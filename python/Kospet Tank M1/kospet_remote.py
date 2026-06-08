import asyncio
import ctypes
from ctypes import wintypes
from datetime import datetime

from bleak import BleakScanner, BleakClient

TARGET_NAME = "TANK M1"
MAX_SCAN_ATTEMPTS = 10
SCAN_TIMEOUT_SECONDS = 10

FEE3_CHAR = "0000fee3-0000-1000-8000-00805f9b34fb"

SKIP_NOTIFY_CHARS = {
    "00002a05-0000-1000-8000-00805f9b34fb",
}

VK_VOLUME_UP = 0xAF
VK_VOLUME_DOWN = 0xAE
VK_MEDIA_PLAY_PAUSE = 0xB3

KEYEVENTF_KEYUP = 0x0002


def log(text: str) -> None:
    now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{now}] {text}")


def hx(data: bytearray | bytes) -> str:
    return bytes(data).hex(" ").upper()


def press_key(vk_code: int) -> None:
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)


def handle_player_packet(data: bytearray | bytes) -> bool:
    b = bytes(data)

    # Player controls:
    # FE EA 20 06 67 01 -> previous  -> volume down
    # FE EA 20 06 67 02 -> next      -> volume up
    # FE EA 20 06 67 06 -> play      -> play/pause
    if len(b) == 6 and b[:5] == bytes.fromhex("FE EA 20 06 67"):
        action_code = b[5]

        if action_code == 0x01:
            log(f"Watch player: previous -> Volume down raw={hx(b)}")
            press_key(VK_VOLUME_DOWN)
            return True

        if action_code == 0x02:
            log(f"Watch player: next -> Volume up raw={hx(b)}")
            press_key(VK_VOLUME_UP)
            return True

        if action_code == 0x06:
            log(f"Watch player: play -> Play/Pause raw={hx(b)}")
            press_key(VK_MEDIA_PLAY_PAUSE)
            return True

        log(f"Unknown player action code=0x{action_code:02X} raw={hx(b)}")
        return True

    return False


async def find_watch_once(attempt: int):
    print(f"Scanning attempt {attempt}/{MAX_SCAN_ATTEMPTS}...")

    devices = await BleakScanner.discover(
        timeout=SCAN_TIMEOUT_SECONDS,
        return_adv=True,
    )

    for address, (device, adv) in devices.items():
        name = device.name or adv.local_name or "Unknown"
        print(f"{name:30} {address} RSSI={adv.rssi}")

        if TARGET_NAME.upper() in name.upper():
            return device

    return None


async def find_watch():
    for attempt in range(1, MAX_SCAN_ATTEMPTS + 1):
        device = await find_watch_once(attempt)

        if device:
            return device

        if attempt < MAX_SCAN_ATTEMPTS:
            print("Watch not found. Retrying...\n")
            await asyncio.sleep(2)

    return None


async def wait_for_quit():
    print("\nRemote active.")
    print("Watch controls:")
    print("  Previous -> Volume down")
    print("  Next     -> Volume up")
    print("  Play     -> Play/Pause")
    print("\nType q and press Enter to quit. Ctrl+C also works.\n")

    while True:
        try:
            text = await asyncio.to_thread(input, "")
        except asyncio.CancelledError:
            return

        if text.strip().lower() == "q":
            return


async def main():
    device = await find_watch()

    if not device:
        print(f"Watch not found after {MAX_SCAN_ATTEMPTS} attempts.")
        return

    print(f"\nConnecting to {device.name} / {device.address}...")

    async with BleakClient(device, timeout=60, pair=True) as client:
        print("Connected:", client.is_connected)

        notify_chars = []

        for service in client.services:
            for char in service.characteristics:
                uuid = char.uuid.lower()

                if uuid in SKIP_NOTIFY_CHARS:
                    continue

                if "notify" in char.properties or "indicate" in char.properties:
                    notify_chars.append(char.uuid)

        print("\nNotify/indicate characteristics:")
        for uuid in notify_chars:
            print(" ", uuid)

        def make_callback(uuid: str):
            def callback(sender, data):
                uuid_l = uuid.lower()

                if uuid_l == FEE3_CHAR:
                    handled = handle_player_packet(data)
                    if not handled:
                        # Keep this quiet-ish, but useful while testing.
                        raw = hx(data)
                        if raw.startswith("FE EA 20 06 67"):
                            log(f"Unhandled player-like packet raw={raw}")

            return callback

        print("\nStarting notifications...")

        active_notify_chars = []

        for uuid in notify_chars:
            try:
                await client.start_notify(uuid, make_callback(uuid))
                active_notify_chars.append(uuid)
                print("OK ", uuid)
            except Exception as e:
                print("FAIL", uuid, e)

        try:
            await wait_for_quit()
        finally:
            print("\nStopping notifications...")

            for uuid in active_notify_chars:
                try:
                    await client.stop_notify(uuid)
                except Exception:
                    pass

            print("Done.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nQuit.")