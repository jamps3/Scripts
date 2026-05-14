import asyncio
from datetime import datetime
from bleak import BleakScanner, BleakClient

TARGET_NAME = "TANK M1"
MAX_SCAN_ATTEMPTS = 10
SCAN_TIMEOUT_SECONDS = 10

BATTERY_CHAR = "00002a19-0000-1000-8000-00805f9b34fb"
HEART_RATE_CHAR = "00002a37-0000-1000-8000-00805f9b34fb"


def hx(data: bytearray | bytes) -> str:
    return bytes(data).hex(" ").upper()


def parse_heart_rate(data: bytearray | bytes) -> int | None:
    b = bytes(data)

    if not b:
        return None

    flags = b[0]
    is_uint16 = flags & 0x01

    if is_uint16:
        if len(b) < 3:
            return None
        return int.from_bytes(b[1:3], byteorder="little")

    if len(b) < 2:
        return None

    return b[1]


def parse_kospet_packet(data: bytearray | bytes) -> dict:
    b = bytes(data)
    raw = hx(b)

    # Camera shutter / remote camera button
    # Example: FE EA 20 05 66
    if b == bytes.fromhex("FE EA 20 05 66"):
        return {
            "type": "shutter",
            "raw": raw,
        }

    # Heart rate / status/progress:
    # FE EA 20 06 6D 00 -> status/progress/no value
    # FE EA 20 06 6D 5C -> heart rate 92 bpm
    if len(b) == 6 and b[:5] == bytes.fromhex("FE EA 20 06 6D"):
        value = b[5]

        if value == 0x00:
            return {
                "type": "blood_pressure_status",
                "raw": raw,
            }

        return {
            "type": "heart_rate_proprietary",
            "bpm": value,
            "raw": raw,
        }

    # Blood pressure result / abort:
    # FE EA 20 08 69 00 86 4F -> 134/79
    # FE EA 20 08 69 00 88 4A -> 136/74
    # FE EA 20 08 69 00 FF FF -> aborted/failed
    if len(b) == 8 and b[:6] == bytes.fromhex("FE EA 20 08 69 00"):
        systolic = b[6]
        diastolic = b[7]

        if systolic == 0xFF and diastolic == 0xFF:
            return {
                "type": "blood_pressure_aborted",
                "raw": raw,
            }

        return {
            "type": "blood_pressure",
            "systolic": systolic,
            "diastolic": diastolic,
            "raw": raw,
        }

    return {
        "type": "unknown",
        "raw": raw,
    }


def describe_packet(uuid: str, data: bytearray | bytes) -> str:
    b = bytes(data)
    raw = hx(b)
    uuid = uuid.lower()

    if uuid == BATTERY_CHAR:
        if len(b) >= 1:
            return f"Battery: {b[0]}% raw={raw}"

    if uuid == HEART_RATE_CHAR:
        bpm = parse_heart_rate(b)
        return f"Heart rate standard BLE: {bpm} bpm raw={raw}"

    parsed = parse_kospet_packet(b)

    if parsed["type"] == "blood_pressure":
        return (
            f"Blood pressure: "
            f"{parsed['systolic']}/{parsed['diastolic']} mmHg "
            f"raw={parsed['raw']}"
        )

    if parsed["type"] == "blood_pressure_aborted":
        return f"Blood pressure aborted/failed raw={parsed['raw']}"

    if parsed["type"] == "blood_pressure_status":
        return f"Blood pressure status/progress raw={parsed['raw']}"

    if parsed["type"] == "heart_rate_proprietary":
        return f"Heart rate: {parsed['bpm']} bpm raw={parsed['raw']}"

    if parsed["type"] == "shutter":
        return f"Camera shutter pressed raw={parsed['raw']}"

    return f"Unknown packet from {uuid}: raw={raw}"


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
    print("\nListening indefinitely.")
    print("Type q and press Enter to quit. Ctrl+C also works.\n")

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
                if "notify" in char.properties or "indicate" in char.properties:
                    notify_chars.append(char.uuid)

        print("\nNotify/indicate characteristics:")
        for uuid in notify_chars:
            print(" ", uuid)

        def make_callback(uuid: str):
            def callback(sender, data):
                now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                message = describe_packet(uuid, data)
                print(f"[{now}] {message}")

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