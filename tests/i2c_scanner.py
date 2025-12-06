#!/usr/bin/env python3
"""
I2C Scanner for debugging FRAM connection
Scans I2C bus and reports found devices
"""

from machine import I2C, Pin
import time

def scan_i2c():
    print("=== I2C Scanner ===")
    
    # Try different I2C configurations
    i2c_configs = [
        {"id": 1, "sda": 16, "scl": 17, "freq": 100000, "name": "I2C1 (GP16/GP17) 100kHz"},
        {"id": 1, "sda": 16, "scl": 17, "freq": 400000, "name": "I2C1 (GP16/GP17) 400kHz"},
        {"id": 0, "sda": 16, "scl": 17, "freq": 100000, "name": "I2C0 (GP16/GP17) 100kHz"},
    ]
    
    for config in i2c_configs:
        print(f"\nTrying {config['name']}...")
        try:
            i2c = I2C(config["id"], sda=Pin(config["sda"]), scl=Pin(config["scl"]), freq=config["freq"])
            
            # Scan for devices
            devices = i2c.scan()
            
            if devices:
                print(f"   Found {len(devices)} device(s):")
                for device in devices:
                    print(f"   - Address: 0x{device:02x} ({device})")
                    if device == 0x50:
                        print(f"     ✓ This is the expected FRAM address!")
                    elif device == 0x51:
                        print(f"     ⚠ This might be FRAM with A0=1")
                    elif device == 0x52:
                        print(f"     ⚠ This might be FRAM with A1=1")
                    elif device == 0x53:
                        print(f"     ⚠ This might be FRAM with A0=1, A1=1")
                    elif device == 0x54:
                        print(f"     ⚠ This might be FRAM with A2=1")
                    elif device == 0x55:
                        print(f"     ⚠ This might be FRAM with A0=1, A2=1")
                    elif device == 0x56:
                        print(f"     ⚠ This might be FRAM with A1=1, A2=1")
                    elif device == 0x57:
                        print(f"     ⚠ This might be FRAM with A0=1, A1=1, A2=1")
            else:
                print("   No devices found")
                
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n=== Expected FRAM Address ===")
    print("With A0-A2 pins grounded, FRAM should be at address 0x50")
    print("Check your wiring:")
    print("  - VCC (Pin 8) -> 3.3V")
    print("  - GND (Pin 4) -> GND")
    print("  - SDA (Pin 5) -> GP16")
    print("  - SCL (Pin 6) -> GP17")
    print("  - WP (Pin 7) -> GND (write enabled)")
    print("  - A0-A2 (Pins 1-3) -> GND (address 0x50)")

if __name__ == "__main__":
    scan_i2c() 