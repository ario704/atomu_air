#!/usr/bin/env python3
"""
Sleep Mode Test Script
Tests the 5-second touch hold functionality for entering/exiting sleep mode
"""

from machine import Pin
import utime as time

def test_sleep_mode():
    """Test the sleep mode functionality"""
    print("=== Sleep Mode Test ===")
    print("This test will:")
    print("1. Monitor touch button (GP2) for 5-second holds")
    print("2. Simulate entering sleep mode")
    print("3. Simulate exiting sleep mode")
    print("Press Ctrl+C to stop")
    print()
    
    # Initialize touch pin
    touch_pin = Pin(2, Pin.IN, Pin.PULL_UP)
    
    # State variables
    sleep_mode = False
    touch_hold_start = None
    TOUCH_SLEEP_HOLD_TIME = 5000  # 5 seconds
    last_touch = 1  # Start as released (PULL_UP)
    
    print("Monitoring touch button (GP2)...")
    print("Hold for 5 seconds to toggle sleep mode")
    print("Touch: RELEASED | Sleep: OFF")
    
    while True:
        current_touch = touch_pin.value()
        now = time.ticks_ms()
        
        # Handle touch press (rising edge - touch sends 3.3V when pressed)
        if last_touch == 0 and current_touch == 1:
            touch_hold_start = now
            print(f"[{now}] Touch PRESSED - starting hold timer")
        
        # Handle touch release (falling edge)
        elif last_touch == 1 and current_touch == 0:
            if touch_hold_start is not None:
                hold_time = time.ticks_diff(now, touch_hold_start)
                print(f"[{now}] Touch RELEASED after {hold_time}ms")
                
                if hold_time >= TOUCH_SLEEP_HOLD_TIME:
                    if sleep_mode:
                        sleep_mode = False
                        print(f"[{now}] ✓ EXITING SLEEP MODE")
                    else:
                        sleep_mode = True
                        print(f"[{now}] ✓ ENTERING SLEEP MODE")
                else:
                    print(f"[{now}] Hold time too short ({hold_time}ms < {TOUCH_SLEEP_HOLD_TIME}ms)")
                
                touch_hold_start = None
        
        # Handle touch hold detection (while pressed)
        if current_touch == 1 and touch_hold_start is not None:  # Touch is pressed (HIGH)
            hold_time = time.ticks_diff(now, touch_hold_start)
            if hold_time >= TOUCH_SLEEP_HOLD_TIME:
                if sleep_mode:
                    sleep_mode = False
                    print(f"[{now}] ✓ EXITING SLEEP MODE (while held)")
                else:
                    sleep_mode = True
                    print(f"[{now}] ✓ ENTERING SLEEP MODE (while held)")
                touch_hold_start = None
        
        last_touch = current_touch
        
        # Show current status
        status = "ON" if sleep_mode else "OFF"
        touch_status = "PRESSED" if current_touch == 1 else "RELEASED"  # HIGH = pressed
        print(f"Touch: {touch_status:8} | Sleep: {status:3}", end="\r")
        
        time.sleep(0.1)

if __name__ == "__main__":
    try:
        test_sleep_mode()
    except KeyboardInterrupt:
        print("\n\nTest stopped by user")
    except Exception as e:
        print(f"\n\nTest error: {e}") 