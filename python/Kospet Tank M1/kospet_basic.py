import asyncio
from bleak import BleakScanner, BleakClient

TARGET_NAME = "TANK M1"

BATTERY_CHAR = "00002a19-0000-1000-8000-00805f9b34fb"
DEVICE_NAME_CHAR = "00002a00-0000-1000-8000-00805f9b34fb"

HEART_RATE_MEASUREMENT_CHAR = "00002a37-0000-1000-8000-00805f9b34fb"
HEART_RATE_CONTROL_CHAR = "00002a39-0000-1000-8000-00805f9b34fb"

PROPRIETARY_WRITE_CHAR = "00006387-3c17-d293-8e48-14fe2e4da212"
PROPRIETARY_NOTIFY_CHAR = "00006487-3c17-d293-8e48-14fe2e4da212"


def parse_heart_rate(data: bytearray) -> int | None:
    if not data:
        return None

    flags = data[0]
    is_uint16 = flags & 0x01

    if is_uint16:
        if len(data) < 3:
            return None
        return int.from_bytes(data[1:3], byteorder="little")

    if len(data) < 2:
        return None
    return data[1]


def hex_bytes(data: bytearray) -> str:
    return " ".join(f"{b:02X}" for b in data)


async def find_watch():
    print("Scanning...")
    devices = await BleakScanner.discover(timeout=15, return_adv=True)

    for address, (device, adv) in devices.items():
        name = device.name or adv.local_name or "Unknown"
        print(f"{name:30} {address} RSSI={adv.rssi}")

        if TARGET_NAME.upper() in name.upper():
            return device

    return None


async def main():
    device = await find_watch()

    if not device:
        print("Watch not found.")
        return

    print(f"\nConnecting to {device.name} / {device.address}...")

    async with BleakClient(device, timeout=60, pair=True) as client:
        print("Connected:", client.is_connected)

        # Read device name
        try:
            raw_name = await client.read_gatt_char(DEVICE_NAME_CHAR)
            print("Device name:", raw_name.decode(errors="replace"))
        except Exception as e:
            print("Could not read device name:", e)

        # Read battery
        try:
            battery = await client.read_gatt_char(BATTERY_CHAR)
            print(f"Battery: {battery[0]}%")
        except Exception as e:
            print("Could not read battery:", e)

        # Battery notifications
        def battery_callback(sender, data):
            print(f"[BATTERY notify] {data[0]}% raw={hex_bytes(data)}")

        # Heart-rate notifications
        def heart_rate_callback(sender, data):
            bpm = parse_heart_rate(data)
            print(f"[HEART notify] bpm={bpm} raw={hex_bytes(data)}")

        # Proprietary notifications
        def proprietary_callback(sender, data):
            print(f"[PROPRIETARY notify] {hex_bytes(data)}")

        print("\nStarting notifications...")

        await client.start_notify(BATTERY_CHAR, battery_callback)
        await client.start_notify(HEART_RATE_MEASUREMENT_CHAR, heart_rate_callback)
        await client.start_notify(PROPRIETARY_NOTIFY_CHAR, proprietary_callback)

        print("Notifications active.")
        print("Try opening heart-rate measurement on the watch.")
        print("Listening for 60 seconds...\n")

        await asyncio.sleep(60)

        await client.stop_notify(BATTERY_CHAR)
        await client.stop_notify(HEART_RATE_MEASUREMENT_CHAR)
        await client.stop_notify(PROPRIETARY_NOTIFY_CHAR)

        print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())