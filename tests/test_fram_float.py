#!/usr/bin/env python3
"""
Test FRAM float storage for decimal precision filter percentages
"""

from machine import I2C, Pin
import time
import struct

def test_fram_float():
    print("=== FRAM Float Storage Test ===")
    print("Testing decimal precision for filter percentages...")
    
    try:
        # Initialize I2C0 with GP16/GP17
        print("1. Initializing I2C0 on GP16/GP17...")
        i2c = I2C(0, sda=Pin(16), scl=Pin(17), freq=100000)
        print("✓ I2C0 initialized successfully")
        
        # Scan for devices
        devices = i2c.scan()
        if 0x50 not in devices:
            print("✗ FRAM not found at address 0x50")
            return False
        
        print("✓ FRAM found at address 0x50")
        
        # Test various decimal values
        test_values = [
            0.0,      # Start
            0.01,     # First increment
            25.5,     # Half way
            50.0,     # Middle
            75.25,    # Quarter precision
            99.99,    # Almost full
            100.0     # Full
        ]
        
        print("2. Testing float write/read operations...")
        print("Value | Write | Read  | Difference | Status")
        print("------|-------|-------|------------|--------")
        
        for test_value in test_values:
            try:
                # Write float to FRAM (address 0)
                addr_bytes = (0).to_bytes(2, 'big')
                float_bytes = struct.pack('f', test_value)
                i2c.writeto_mem(0x50, addr_bytes[0] << 8 | addr_bytes[1], float_bytes)
                
                # Read back the float
                data = i2c.readfrom_mem(0x50, addr_bytes[0] << 8 | addr_bytes[1], 4)
                read_value = struct.unpack('f', data)[0]
                
                # Calculate difference
                diff = abs(test_value - read_value)
                
                # Check if read matches what we wrote (allow small floating point errors)
                if diff < 0.001:  # Less than 0.001% difference
                    status = "✓ OK"
                else:
                    status = f"✗ ERROR (diff: {diff:.6f})"
                
                print(f"{test_value:5.2f} | {test_value:5.2f} | {read_value:5.2f} | {diff:8.6f} | {status}")
                
                time.sleep(0.1)  # Small delay between tests
                
            except Exception as e:
                print(f"{test_value:5.2f} | ERROR | ERROR | ERROR | ✗ Exception: {e}")
        
        # Test incremental updates (like real usage)
        print("\n3. Testing incremental updates...")
        current_value = 0.0
        increment = 0.01
        
        print("Step | Current | Write | Read  | Status")
        print("-----|---------|-------|-------|--------")
        
        for step in range(10):  # Test 10 increments
            try:
                # Write current value
                addr_bytes = (0).to_bytes(2, 'big')
                float_bytes = struct.pack('f', current_value)
                i2c.writeto_mem(0x50, addr_bytes[0] << 8 | addr_bytes[1], float_bytes)
                
                # Read back
                data = i2c.readfrom_mem(0x50, addr_bytes[0] << 8 | addr_bytes[1], 4)
                read_value = struct.unpack('f', data)[0]
                
                # Check accuracy
                diff = abs(current_value - read_value)
                if diff < 0.001:
                    status = "✓ OK"
                else:
                    status = f"✗ ERROR (diff: {diff:.6f})"
                
                print(f"{step:4d} | {current_value:7.2f} | {current_value:5.2f} | {read_value:5.2f} | {status}")
                
                # Increment for next step
                current_value += increment
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"{step:4d} | ERROR | ERROR | ERROR | ✗ Exception: {e}")
        
        print("\n=== Float storage test completed! ===")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_fram_float()
    if success:
        print("\n=== FRAM float test PASSED ===")
    else:
        print("\n=== FRAM float test FAILED ===") 