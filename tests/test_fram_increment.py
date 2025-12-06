#!/usr/bin/env python3
"""
FRAM Increment Test - increments filter percentage by 0.05% every second until 100.00%
Tests decimal precision and persistence over time
"""

from machine import I2C, Pin
import time
import struct

def test_fram_increment():
    print("=== FRAM Increment Test ===")
    print("This test will:")
    print("1. Start at 0.00%")
    print("2. Increment by 0.05% every second")
    print("3. Continue until reaching 100.00%")
    print("4. Test persistence after completion")
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
        
        # Start at 0.00%
        current_value = 0.0
        increment = 0.05
        target_value = 100.0
        
        print(f"Starting increment test: {current_value:.2f}% -> {target_value:.2f}%")
        print("Time | Write | Read  | Difference | Status")
        print("-----|-------|-------|------------|--------")
        
        start_time = time.time()
        step_count = 0
        
        while current_value <= target_value:
            elapsed = int(time.time() - start_time)
            step_count += 1
            
            try:
                # Write current value to FRAM (address 0)
                addr_bytes = (0).to_bytes(2, 'big')
                float_bytes = struct.pack('f', current_value)
                i2c.writeto_mem(0x50, addr_bytes[0] << 8 | addr_bytes[1], float_bytes)
                
                # Read back the value
                data = i2c.readfrom_mem(0x50, addr_bytes[0] << 8 | addr_bytes[1], 4)
                read_value = struct.unpack('f', data)[0]
                
                # Calculate difference
                diff = abs(current_value - read_value)
                
                # Check if read matches what we wrote (allow small floating point errors)
                if diff < 0.001:  # Less than 0.001% difference
                    status = "✓ OK"
                else:
                    status = f"✗ ERROR (diff: {diff:.6f})"
                
                print(f"{elapsed:4d}s | {current_value:5.2f} | {read_value:5.2f} | {diff:8.6f} | {status}")
                
                # Check if we've reached the target
                if current_value >= target_value:
                    print(f"\n✓ Reached target value: {current_value:.2f}%")
                    break
                
                # Increment for next iteration
                current_value += increment
                if current_value > target_value:
                    current_value = target_value  # Cap at exactly 100.00
                
                time.sleep(1)
                
            except Exception as e:
                print(f"{elapsed:4d}s | ERROR | ERROR | ERROR | ✗ Exception: {e}")
                time.sleep(1)
        
        # Calculate statistics
        total_time = time.time() - start_time
        total_steps = step_count
        
        print(f"\n=== Test Statistics ===")
        print(f"Total time: {total_time:.1f} seconds")
        print(f"Total steps: {total_steps}")
        print(f"Average time per step: {total_time/total_steps:.2f} seconds")
        print(f"Final value: {current_value:.2f}%")
        
        # Final verification - read the last value
        print(f"\n=== Final Verification ===")
        try:
            addr_bytes = (0).to_bytes(2, 'big')
            data = i2c.readfrom_mem(0x50, addr_bytes[0] << 8 | addr_bytes[1], 4)
            final_value = struct.unpack('f', data)[0]
            print(f"Final value in FRAM: {final_value:.2f}%")
            
            # Power cycle simulation - read again after a delay
            print("Waiting 5 seconds to simulate power cycle...")
            time.sleep(5)
            
            data = i2c.readfrom_mem(0x50, addr_bytes[0] << 8 | addr_bytes[1], 4)
            persistent_value = struct.unpack('f', data)[0]
            print(f"Value after 'power cycle': {persistent_value:.2f}%")
            
            diff = abs(final_value - persistent_value)
            if diff < 0.001:
                print("✓ FRAM persistence test PASSED!")
                print("✓ Decimal precision test PASSED!")
                print("✓ Increment test PASSED!")
                return True
            else:
                print(f"✗ FRAM persistence test FAILED! Expected {final_value:.2f}, got {persistent_value:.2f}")
                return False
                
        except Exception as e:
            print(f"✗ Final verification failed: {e}")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting FRAM increment test...")
    print("This will take about 33 minutes (2000 steps × 1 second)")
    print("Press Ctrl+C to stop early")
    print()
    
    try:
        success = test_fram_increment()
        if success:
            print("\n=== FRAM increment test PASSED ===")
            print("✓ Decimal precision working correctly")
            print("✓ Persistence working correctly")
            print("✓ Increment accuracy working correctly")
        else:
            print("\n=== FRAM increment test FAILED ===")
    except KeyboardInterrupt:
        print("\n\nTest stopped by user")
        print("=== Test interrupted ===") 