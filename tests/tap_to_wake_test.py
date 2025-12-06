#!/usr/bin/env python3
"""
Tap-to-Wake Test Script
Tests the new tap-to-wake functionality where:
1. Hold touch button for 5 seconds to enter sleep mode
2. Single tap while in sleep mode wakes up the device
3. Hold touch button for 5 seconds again to exit sleep mode
"""

from machine import Pin
import utime as time

def test_tap_to_wake():
    """Test the tap-to-wake functionality"""
    print("=== Tap-to-Wake Test ===")
    print("This test will:")
    print("1. Monitor touch button (GP2) for 5-second holds to enter sleep")
    print("2. Test single tap to wake up from sleep mode")
    print("3. Test 5-second hold to exit sleep mode")
    print("Press Ctrl+C to stop")
    print()
    
    # Initialize touch pin
    touch_pin = Pin(2, Pin.IN, Pin.PULL_UP)
    
    # State variables
    sleep_mode = False
    touch_hold_start = None
    TOUCH_SLEEP_HOLD_TIME = 5000  # 5 seconds
    last_touch = 1  # Start as released (PULL_UP)
    last_touch_time = 0
    TOUCH_DEBOUNCE_MS = 200
    
    print("Monitoring touch button (GP2)...")
    print("Touch: RELEASED | Sleep: OFF")
    
    while True:
        current_touch = touch_pin.value()
        now = time.ticks_ms()
        
        # Handle touch press (rising edge - touch sends 3.3V when pressed)
        if last_touch == 0 and current_touch == 1 and time.ticks_diff(now, last_touch_time) > TOUCH_DEBOUNCE_MS:
            touch_hold_start = now
            last_touch_time = now
            print(f"[{now}] Touch PRESSED - starting hold timer")
        
        # Handle touch release (falling edge)
        elif last_touch == 1 and current_touch == 0:
            if touch_hold_start is not None:
                hold_time = time.ticks_diff(now, touch_hold_start)
                print(f"[{now}] Touch RELEASED after {hold_time}ms")
                
                if hold_time >= TOUCH_SLEEP_HOLD_TIME:
                    # Long press - toggle sleep mode
                    if sleep_mode:
                        sleep_mode = False
                        print(f"[{now}] ✓ EXITING SLEEP MODE (long press)")
                    else:
                        sleep_mode = True
                        print(f"[{now}] ✓ ENTERING SLEEP MODE (long press)")
                else:
                    # Short press - handle wake up or mode selection
                    if sleep_mode:
                        # In sleep mode - single tap wakes up
                        sleep_mode = False
                        print(f"[{now}] ✓ WAKING UP FROM SLEEP (single tap)")
                    else:
                        # Not in sleep mode - normal mode selection
                        print(f"[{now}] Short press in normal mode (would cycle modes)")
                
                touch_hold_start = None
        
        last_touch = current_touch
        
        # Show current status
        status = "ON" if sleep_mode else "OFF"
        touch_status = "PRESSED" if current_touch == 1 else "RELEASED"  # HIGH = pressed
        print(f"Touch: {touch_status:8} | Sleep: {status:3}", end="\r")
        
        time.sleep(0.1)

if __name__ == "__main__":
    try:
        test_tap_to_wake()
    except KeyboardInterrupt:
        print("\n\nTest stopped by user")
    except Exception as e:
        print(f"\nError: {e}") 