import asyncio
from datetime import datetime
from bleak import BleakScanner, BleakClient

TARGET_NAME = "TANK M1"
MAX_SCAN_ATTEMPTS = 10
SCAN_TIMEOUT_SECONDS = 10

BATTERY_CHAR = "00002a19-0000-1000-8000-00805f9b34fb"
HEART_RATE_CHAR = "00002a37-0000-1000-8000-00805f9b34fb"
FEE1_CHAR = "0000fee1-0000-1000-8000-00805f9b34fb"
FEA1_CHAR = "0000fea1-0000-1000-8000-00805f9b34fb"

def hx(data: bytearray | bytes) -> str:
    return bytes(data).hex(" ").upper()

def parse_activity_packet(data: bytearray | bytes) -> dict:
    b = bytes(data)
    raw = hx(b)

    # FEA1 appears to wrap the same payload with leading 0x07
    if len(b) == 10 and b[0] == 0x07:
        b = b[1:]

    if len(b) == 9:
        return {
            "type": "activity_live",
            "sequence": b[0],
            "field1": int.from_bytes(b[1:3], "little"),
            "steps_counter": int.from_bytes(b[3:5], "little"),
            "field3": b[5],
            "calories": int.from_bytes(b[6:8], "little"),
            "field5": b[8],
            "raw": raw,
        }

    return {
        "type": "activity_unknown",
        "raw": raw,
    }

def parse_standard_heart_rate(data: bytearray | bytes) -> int | None:
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

    # Single event packets:
    # FE EA 20 05 64 -> camera remote event/opened?
    # FE EA 20 05 66 -> camera shutter pressed
    if len(b) == 5 and b[:4] == bytes.fromhex("FE EA 20 05"):
        event_code = b[4]

        if event_code == 0x64:
            return {
                "type": "camera_remote_event",
                "event_code": event_code,
                "raw": raw,
            }

        if event_code == 0x66:
            return {
                "type": "camera_shutter",
                "event_code": event_code,
                "raw": raw,
            }

        return {
            "type": "single_event",
            "event_code": event_code,
            "raw": raw,
        }

    # Player controls:
    # FE EA 20 06 67 01 -> previous
    # FE EA 20 06 67 02 -> next
    # FE EA 20 06 67 06 -> play
    if len(b) == 6 and b[:5] == bytes.fromhex("FE EA 20 06 67"):
        action_code = b[5]

        actions = {
            0x01: "previous",
            0x02: "next",
            0x06: "play",
        }

        return {
            "type": "player_control",
            "action": actions.get(action_code, "unknown"),
            "action_code": action_code,
            "raw": raw,
        }

    # SpO2 measurement:
    # FE EA 20 06 6B 62 -> SpO2 98%
    if len(b) == 6 and b[:5] == bytes.fromhex("FE EA 20 06 6B"):
        value = b[5]

        if value == 0x00:
            return {
                "type": "spo2_status",
                "raw": raw,
            }

        return {
            "type": "spo2",
            "spo2": value,
            "raw": raw,
        }

    # Heart rate / status:
    # FE EA 20 06 6D 00 -> status/progress/no value
    # FE EA 20 06 6D 5C -> heart rate 92 bpm
    if len(b) == 6 and b[:5] == bytes.fromhex("FE EA 20 06 6D"):
        value = b[5]

        if value == 0x00:
            return {
                "type": "heart_rate_status",
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
        bpm = parse_standard_heart_rate(b)
        return f"Heart rate standard BLE: {bpm} bpm raw={raw}"
    
    if uuid in (FEE1_CHAR, FEA1_CHAR):
        parsed = parse_activity_packet(b)

        if parsed["type"] == "activity_live":
            return (
                f"Activity live: "
                f"seq={parsed['sequence']} "
                f"field1={parsed['field1']} "
                f"steps_counter={parsed['steps_counter']} "
                f"calories={parsed['calories']} kcal "
                f"raw={parsed['raw']}"
            )

        return f"Activity unknown raw={parsed['raw']}"

    parsed = parse_kospet_packet(b)

    packet_type = parsed["type"]

    if packet_type == "camera_remote_event":
        return (
            f"Camera remote event/opened? "
            f"code=0x{parsed['event_code']:02X} raw={parsed['raw']}"
        )

    if packet_type == "camera_shutter":
        return f"Camera shutter pressed raw={parsed['raw']}"

    if packet_type == "single_event":
        return (
            f"Single event packet "
            f"code=0x{parsed['event_code']:02X} raw={parsed['raw']}"
        )

    if packet_type == "player_control":
        return (
            f"Player control: {parsed['action']} "
            f"code=0x{parsed['action_code']:02X} raw={parsed['raw']}"
        )

    if packet_type == "spo2":
        return f"SpO2: {parsed['spo2']}% raw={parsed['raw']}"

    if packet_type == "spo2_status":
        return f"SpO2 status/progress raw={parsed['raw']}"

    if packet_type == "heart_rate_proprietary":
        return f"Heart rate: {parsed['bpm']} bpm raw={parsed['raw']}"

    if packet_type == "heart_rate_status":
        return f"Heart rate status/progress raw={parsed['raw']}"

    if packet_type == "blood_pressure":
        return (
            f"Blood pressure: "
            f"{parsed['systolic']}/{parsed['diastolic']} mmHg "
            f"raw={parsed['raw']}"
        )

    if packet_type == "blood_pressure_aborted":
        return f"Blood pressure aborted/failed raw={parsed['raw']}"

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