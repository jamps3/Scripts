import asyncio
from bleak import BleakScanner

async def main():
    print("Scanning for BLE devices...")

    devices = await BleakScanner.discover(
        timeout=10,
        return_adv=True
    )

    print("\nAll nearby BLE devices:")

    for address, (device, adv) in devices.items():
        name = device.name or adv.local_name or "Unknown"
        rssi = adv.rssi

        print(f"{name:30} {address} RSSI={rssi}")

        if any(word in name.upper() for word in ["KOSPET", "TANK", "M1"]):
            print("  ^ Possible Kospet watch")

asyncio.run(main())