import asyncio
from bleak import BleakScanner, BleakClient

TARGET_NAME = "TANK M1"

async def main():
    print("Scanning...")

    found = None

    devices = await BleakScanner.discover(timeout=15, return_adv=True)

    for address, (device, adv) in devices.items():
        name = device.name or adv.local_name or "Unknown"
        print(f"{name:30} {address} RSSI={adv.rssi}")

        if TARGET_NAME.upper() in name.upper():
            found = device

    if not found:
        print("TANK M1 not found.")
        return

    print(f"\nConnecting to {found.name} / {found.address}...")

    async with BleakClient(found, timeout=60, pair=True) as client:
        print("Connected:", client.is_connected)

        print("\nServices:")
        for service in client.services:
            print(f"\nService: {service.uuid}  {service.description}")
            for char in service.characteristics:
                print(f"  Characteristic: {char.uuid}")
                print(f"    Description: {char.description}")
                print(f"    Properties:  {char.properties}")

asyncio.run(main())