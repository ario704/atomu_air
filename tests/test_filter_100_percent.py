#!/usr/bin/env python3
"""
Test script to verify filter reaches 100% correctly
This script simulates motor operation to increment filter usage to 100%
"""

from machine import Pin
import utime as time
from fram import init_fram, write_filter_percent_fram, read_filter_percent_fram

def test_filter_to_100_percent():
    """Test that filter usage correctly reaches 100%"""
    print("=== Filter 100% Test ===")
    
    # Initialize FRAM
    print("1. Initializing FRAM...")
    if not init_fram():
        print("✗ FRAM initialization failed")
        return False
    print("✓ FRAM initialized")
    
    # Reset filter to 0%
    print("2. Resetting filter to 0%...")
    write_filter_percent_fram(0.0)
    filter_percent = read_filter_percent_fram()
    print(f"✓ Filter reset to {filter_percent:.2f}%")
    
    # Simulate motor operation to increment filter
    print("3. Simulating motor operation...")
    print("   - Motor speed: 60% (high mode)")
    print("   - Increment: 60/30 = 2.0% per second")
    print("   - Time to reach 100%: 50 seconds")
    
    motor_speed = 60  # High mode
    increment = motor_speed / 30.0
    seconds_to_100 = 100.0 / increment
    
    print(f"   - Increment per second: {increment:.2f}%")
    print(f"   - Seconds to reach 100%: {seconds_to_100:.1f}s")
    
    # Fast simulation (1 second = 0.1 seconds for testing)
    simulation_speed = 10  # 10x faster
    actual_seconds = seconds_to_100 / simulation_speed
    
    print(f"   - Fast simulation: {actual_seconds:.1f} seconds")
    print("   - Starting simulation...")
    
    start_time = time.ticks_ms()
    last_increment = start_time
    increment_interval = 100  # 0.1 seconds in milliseconds
    
    while filter_percent < 100.0:
        now = time.ticks_ms()
        
        if time.ticks_diff(now, last_increment) >= increment_interval:
            filter_percent += increment
            if filter_percent > 100.0:
                filter_percent = 100.0
            
            write_filter_percent_fram(filter_percent)
            elapsed = time.ticks_diff(now, start_time) / 1000.0
            print(f"   - Time: {elapsed:.1f}s, Filter: {filter_percent:.2f}%")
            
            last_increment = now
        
        time.sleep(0.01)  # 10ms delay
    
    print(f"✓ Filter reached {filter_percent:.2f}% in {time.ticks_diff(time.ticks_ms(), start_time)/1000:.1f} seconds")
    
    # Verify filter is at 100%
    final_filter = read_filter_percent_fram()
    if final_filter >= 100.0:
        print("✓ Filter successfully reached 100%")
        print("   - The system should now wait for reset button to be held for 3 seconds")
        return True
    else:
        print(f"✗ Filter failed to reach 100%, stopped at {final_filter:.2f}%")
        return False

if __name__ == "__main__":
    success = test_filter_to_100_percent()
    if success:
        print("\n=== Test PASSED ===")
        print("Now run test_filter_reset.py to test the reset functionality")
    else:
        print("\n=== Test FAILED ===") 