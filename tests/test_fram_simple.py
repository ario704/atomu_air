#!/usr/bin/env python3
"""
Simple FRAM test script for Pico
Run this directly on the Pico to test FRAM functionality
"""

from machine import I2C, Pin
import time

def test_fram():
    print("=== Simple FRAM Test ===")
    
    try:
        # Initialize I2C0 with GP16/GP17
        print("1. Initializing I2C0 on GP16/GP17...")
        i2c = I2C(0, sda=Pin(16), scl=Pin(17), freq=100000)
        print("   I2C0 initialized successfully")
        
        # Scan for devices
        print("2. Scanning I2C devices...")
        devices = i2c.scan()
        print(f"   Found {len(devices)} device(s):")
        for device in devices:
            print(f"   - Address: 0x{device:02x} ({device})")
        
        # Test FRAM communication
        print("3. Testing FRAM communication...")
        if 0x50 in devices:
            print("   FRAM found at address 0x50")
            
            # Try to read from address 0
            try:
                # Send 2-byte address (big-endian) - address 0
                addr_bytes = (0).to_bytes(2, 'big')
                data = i2c.readfrom_mem(0x50, addr_bytes[0] << 8 | addr_bytes[1], 1)
                print(f"   Read from address 0: 0x{data[0]:02x}")
                
                # Try to write and read back
                test_value = 0xAB
                print(f"4. Writing test value 0x{test_value:02x} to address 0...")
                i2c.writeto_mem(0x50, addr_bytes[0] << 8 | addr_bytes[1], bytes([test_value]))
                
                # Read back
                data = i2c.readfrom_mem(0x50, addr_bytes[0] << 8 | addr_bytes[1], 1)
                print(f"   Read back: 0x{data[0]:02x}")
                
                if data[0] == test_value:
                    print("   ✓ FRAM read/write test PASSED!")
                    return True
                else:
                    print(f"   ✗ FRAM read/write test FAILED! Expected 0x{test_value:02x}, got 0x{data[0]:02x}")
                    return False
                    
            except Exception as e:
                print(f"   ✗ FRAM communication failed: {e}")
                return False
        else:
            print("   ✗ FRAM not found at address 0x50")
            return False
            
    except Exception as e:
        print(f"   ✗ I2C initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = test_fram()
    if success:
        print("\n=== FRAM test PASSED ===")
    else:
        print("\n=== FRAM test FAILED ===") 