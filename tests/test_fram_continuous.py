#!/usr/bin/env python3
"""
Continuous FRAM test - writes a value, increments it every second, and reads it back
Run this on the Pico to test FRAM reliability over time
"""

from machine import I2C, Pin
import time

def continuous_fram_test():
    print("=== Continuous FRAM Test ===")
    print("This test will:")
    print("1. Write an initial value to FRAM")
    print("2. Increment it by 1 every second")
    print("3. Read it back to verify persistence")
    print("4. Continue for 30 seconds")
    print("Press Ctrl+C to stop early")
    print()
    
    try:
        # Initialize I2C0 with GP16/GP17
        print("Initializing I2C0 on GP16/GP17...")
        i2c = I2C(0, sda=Pin(16), scl=Pin(17), freq=100000)
        print("✓ I2C0 initialized successfully")
        
        # Scan for devices
        devices = i2c.scan()
        if 0x50 not in devices:
            print("✗ FRAM not found at address 0x50")
            return False
        
        print("✓ FRAM found at address 0x50")
        
        # Start with value 1
        current_value = 1
        test_duration = 30  # seconds
        start_time = time.time()
        
        print(f"Starting continuous test for {test_duration} seconds...")
        print("Time | Write | Read  | Status")
        print("-----|-------|-------|--------")
        
        while time.time() - start_time < test_duration:
            elapsed = int(time.time() - start_time)
            
            try:
                # Write current value to FRAM (address 0)
                addr_bytes = (0).to_bytes(2, 'big')
                i2c.writeto_mem(0x50, addr_bytes[0] << 8 | addr_bytes[1], bytes([current_value]))
                
                # Read back the value
                data = i2c.readfrom_mem(0x50, addr_bytes[0] << 8 | addr_bytes[1], 1)
                read_value = data[0]
                
                # Check if read matches what we wrote
                if read_value == current_value:
                    status = "✓ OK"
                else:
                    status = f"✗ ERROR (expected {current_value}, got {read_value})"
                
                print(f"{elapsed:4d}s | {current_value:5d} | {read_value:5d} | {status}")
                
                # Increment for next iteration
                current_value += 1
                if current_value > 255:  # Wrap around to avoid overflow
                    current_value = 1
                
                time.sleep(1)
                
            except Exception as e:
                print(f"{elapsed:4d}s | ERROR | ERROR | ✗ Exception: {e}")
                time.sleep(1)
        
        print("\n=== Test completed! ===")
        
        # Final verification - read the last value
        try:
            addr_bytes = (0).to_bytes(2, 'big')
            data = i2c.readfrom_mem(0x50, addr_bytes[0] << 8 | addr_bytes[1], 1)
            final_value = data[0]
            print(f"Final value in FRAM: {final_value}")
            
            # Power cycle simulation - read again after a delay
            print("Waiting 3 seconds to simulate power cycle...")
            time.sleep(3)
            
            data = i2c.readfrom_mem(0x50, addr_bytes[0] << 8 | addr_bytes[1], 1)
            persistent_value = data[0]
            print(f"Value after 'power cycle': {persistent_value}")
            
            if persistent_value == final_value:
                print("✓ FRAM persistence test PASSED!")
                return True
            else:
                print(f"✗ FRAM persistence test FAILED! Expected {final_value}, got {persistent_value}")
                return False
                
        except Exception as e:
            print(f"✗ Final verification failed: {e}")
            return False
            
    except Exception as e:
        print(f"✗ Test initialization failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting continuous FRAM test...")
    print("Press Ctrl+C to stop early")
    print()
    
    try:
        success = continuous_fram_test()
        if success:
            print("\n=== Continuous FRAM test PASSED ===")
        else:
            print("\n=== Continuous FRAM test FAILED ===")
    except KeyboardInterrupt:
        print("\n\nTest stopped by user")
        print("=== Test interrupted ===") 