import asyncio
from bleak import BleakScanner, BleakClient
from datetime import datetime

TARGET_NAME = "TANK M1"
CMD_CHAR = "0000fee3-0000-1000-8000-00805f9b34fb"

def hx(data):
    return bytes(data).hex(" ").upper()

def make_packet(cmd: int, payload: bytes = b"") -> bytes:
    length = len(payload) + 4
    header = bytes.fromhex("FE EA 10")
    return header + bytes([length, cmd]) + payload

def now_timestamp() -> bytes:
    ts = int(datetime.now().timestamp())
    return ts.to_bytes(4, "little")

async def main():
    print("Scanning...")
    devices = await BleakScanner.discover(timeout=10, return_adv=True)
    device = next((d for a, (d, adv) in devices.items() if TARGET_NAME.upper() in (d.name or "").upper()), None)
    if not device:
        print("Watch not found")
        return

    print(f"Connecting to {device.name}...")
    async with BleakClient(device) as client:
        print("Connected")

        def cb(sender, data):
            print(f"<- {hx(data)}")

        await client.start_notify(CMD_CHAR, cb)

        # 1. Sync time
        pkt = make_packet(0x31, now_timestamp() + b"\x08")
        print(f"-> {hx(pkt)} (sync time)")
        await client.write_gatt_char(CMD_CHAR, pkt, response=False)

        await asyncio.sleep(1)

        # 2. Query heart rate
        pkt = make_packet(0x2f)
        print(f"-> {hx(pkt)} (query heart rate)")
        await client.write_gatt_char(CMD_CHAR, pkt, response=False)

        print("\nListening 30s...")
        await asyncio.sleep(30)

        await client.stop_notify(CMD_CHAR)

if __name__ == "__main__":
    asyncio.run(main())
