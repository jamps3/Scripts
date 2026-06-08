import asyncio
from bleak import BleakScanner, BleakClient
from datetime import datetime

TARGET_NAME = "TANK M1"
HARDCODED_ADDRESS = "F9:4D:8C:F2:6D:7D"
MAX_SCAN_ATTEMPTS = 10
SCAN_TIMEOUT_SECONDS = 10

CMD_WRITE = "0000fee2-0000-1000-8000-00805f9b34fb"
CMD_NOTIFY = "0000fee3-0000-1000-8000-00805f9b34fb"

def hx(data):
    return bytes(data).hex(" ").upper()

def make_packet(cmd: int, payload: bytes = b"") -> bytes:
    length = len(payload) + 4
    return bytes.fromhex("FE EA 10") + bytes([length, cmd]) + payload

def now_ts() -> bytes:
    return int(datetime.now().timestamp()).to_bytes(4, "little")

async def find_watch_once(attempt: int):
    print(f"Scanning attempt {attempt}/{MAX_SCAN_ATTEMPTS}...")
    devices = await BleakScanner.discover(timeout=SCAN_TIMEOUT_SECONDS, return_adv=True)
    for address, (device, adv) in devices.items():
        name = device.name or adv.local_name or "Unknown"
        print(f"{name:30} {address} RSSI={adv.rssi}")
        if TARGET_NAME.upper() in name.upper():
            return device
    return None

async def find_watch():
    if HARDCODED_ADDRESS:
        print(f"Using hardcoded address: {HARDCODED_ADDRESS}")
        return HARDCODED_ADDRESS

    for attempt in range(1, MAX_SCAN_ATTEMPTS + 1):
        device = await find_watch_once(attempt)
        if device:
            return device
        if attempt < MAX_SCAN_ATTEMPTS:
            print("Watch not found. Retrying...\n")
            await asyncio.sleep(2)
    return None

async def main():
    device = await find_watch()
    if not device:
        print(f"Watch not found after {MAX_SCAN_ATTEMPTS} attempts.")
        return

    dev_name = device if isinstance(device, str) else device.name
    print(f"Connecting to {dev_name}...")
    async with BleakClient(device) as client:
        print("Connected. Discovering characteristics...")
        for s in client.services:
            for c in s.characteristics:
                if "fee" in c.uuid:
                    print(f"  {c.uuid}  props={c.properties}")

        def cb(sender, data):
            print(f"<- {hx(data)}")

        try:
            await client.start_notify(CMD_NOTIFY, cb)
        except Exception as e:
            print("Notify on fee3 failed:", e)

        # Try sync time on fee2
        pkt = make_packet(0x31, now_ts() + b"\x08")
        print(f"-> {hx(pkt)} (sync time)")
        await client.write_gatt_char(CMD_WRITE, pkt, response=False)

        await asyncio.sleep(1)

        # Query heart rate
        pkt = make_packet(0x2f)
        print(f"-> {hx(pkt)} (query hr)")
        await client.write_gatt_char(CMD_WRITE, pkt, response=False)

        print("\nListening 300s...")
        await asyncio.sleep(300)

        await client.stop_notify(CMD_NOTIFY)

if __name__ == "__main__":
    asyncio.run(main())
