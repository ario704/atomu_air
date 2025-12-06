#!/usr/bin/env python3
"""
Test script for filter reset functionality
This script simulates the filter reaching 100% and tests the reset button behavior
"""

from machine import Pin
import utime as time
from fram import init_fram, write_filter_percent_fram, read_filter_percent_fram

def test_filter_reset():
    """Test the filter reset functionality"""
    print("=== Filter Reset Test ===")
    
    # Initialize FRAM
    print("1. Initializing FRAM...")
    if not init_fram():
        print("✗ FRAM initialization failed")
        return False
    print("✓ FRAM initialized")
    
    # Set filter to 100%
    print("2. Setting filter to 100%...")
    write_filter_percent_fram(100.0)
    filter_percent = read_filter_percent_fram()
    print(f"✓ Filter set to {filter_percent:.2f}%")
    
    # Simulate the reset button behavior
    print("3. Simulating reset button press...")
    reset_pin = Pin(3, Pin.IN, Pin.PULL_UP)
    
    print("   - Press and hold the reset button (GP3) for 3 seconds")
    print("   - The system should detect the button press and start timing")
    print("   - After 3 seconds, the filter should reset to 0%")
    
    # Wait for user to press reset button
    print("   - Waiting for reset button press...")
    
    reset_start_time = None
    reset_held = False
    
    while not reset_held:
        # Check if reset button is pressed
        if reset_pin.value() == 0:  # Button pressed (active low)
            if reset_start_time is None:
                reset_start_time = time.ticks_ms()
                print("   ✓ Reset button pressed, starting timer")
        else:
            # Button released, reset timer
            if reset_start_time is not None:
                print("   - Reset button released, resetting timer")
                reset_start_time = None
        
        # Check if button has been held for 3 seconds
        if reset_start_time is not None:
            hold_time = time.ticks_diff(time.ticks_ms(), reset_start_time)
            remaining = 3000 - hold_time
            if remaining > 0 and remaining % 1000 < 100:  # Print every second
                print(f"   - Hold time: {hold_time//1000}s, remaining: {remaining//1000}s")
            if hold_time >= 3000:  # 3 seconds
                reset_held = True
                print("   ✓ Reset button held for 3 seconds - resetting filter")
        
        time.sleep(0.1)
    
    # Reset filter percentage
    print("4. Resetting filter to 0%...")
    write_success = write_filter_percent_fram(0.0)
    if not write_success:
        print("✗ Failed to write 0.0 to FRAM")
        return False
    
    # Add a small delay to ensure write completes
    time.sleep(0.1)
    
    print("5. Checking filter reset...")
    filter_percent = read_filter_percent_fram()
    print(f"   - Read back from FRAM: {filter_percent:.2f}%")
    
    if filter_percent == 0.0:
        print(f"✓ Filter successfully reset to {filter_percent:.2f}%")
        return True
    else:
        print(f"✗ Filter reset failed, still at {filter_percent:.2f}%")
        return False

if __name__ == "__main__":
    success = test_filter_reset()
    if success:
        print("\n=== Test PASSED ===")
    else:
        print("\n=== Test FAILED ===") 