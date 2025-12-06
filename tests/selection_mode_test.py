"""
Test script for selection mode functionality
Tests the mode selection system where:
1. Touch shows selected mode (full icon)
2. Touch again confirms and locks mode for 3 seconds
3. Then becomes active
"""

from machine import Pin
import utime as time

# Pin setup
TOUCH_PIN = 2
touch_pin = Pin(TOUCH_PIN, Pin.IN, Pin.PULL_UP)

# Test state
mode_idx = 0
MODES = ["low", "medium", "high", "automatic"]
selecting_mode = False
mode_selection_start = None
MODE_SELECTION_TIMEOUT = 3000  # 3 seconds
last_touch = 1  # Start as released (PULL_UP)
last_touch_time = 0
TOUCH_DEBOUNCE_MS = 200

print("=== Selection Mode Test ===")
print("Touch behavior:")
print("1. Short touch: Enter selection mode")
print("2. Short touch again: Confirm and lock mode")
print("3. Wait 3 seconds: Auto-cycle to next mode")
print("4. Long touch (5s): Toggle sleep mode")
print()

def test_touch_handling():
    global mode_idx, selecting_mode, mode_selection_start, last_touch, last_touch_time
    
    current_touch = touch_pin.value()
    now = time.ticks_ms()
    
    # Handle touch press (rising edge)
    if last_touch == 0 and current_touch == 1 and time.ticks_diff(now, last_touch_time) > TOUCH_DEBOUNCE_MS:
        print(f"[{now}] Touch pressed")
        last_touch_time = now
    
    # Handle touch release (falling edge)
    elif last_touch == 1 and current_touch == 0:
        hold_time = time.ticks_diff(now, last_touch_time)
        print(f"[{now}] Touch released after {hold_time}ms")
        
        if hold_time >= 5000:  # 5 seconds for sleep
            print("  -> Long press detected (sleep mode toggle)")
        else:
            # Short press - handle mode selection
            if not selecting_mode:
                # First touch - enter selection mode
                selecting_mode = True
                mode_selection_start = now
                print(f"  -> Entering selection mode for: {MODES[mode_idx]}")
            else:
                # Second touch - confirm mode selection
                selecting_mode = False
                mode_selection_start = None
                print(f"  -> Mode confirmed and locked: {MODES[mode_idx]}")
    
    last_touch = current_touch
    
    # Check if mode selection timeout has expired
    if selecting_mode and mode_selection_start is not None:
        if time.ticks_diff(now, mode_selection_start) >= MODE_SELECTION_TIMEOUT:
            # Timeout - cycle to next mode
            mode_idx = (mode_idx + 1) % len(MODES)
            mode_selection_start = now
            print(f"[{now}] Mode selection timeout - cycling to: {MODES[mode_idx]}")
    
    # Display current state
    status = f"Mode: {MODES[mode_idx]}"
    if selecting_mode:
        remaining = MODE_SELECTION_TIMEOUT - time.ticks_diff(now, mode_selection_start)
        status += f" (SELECTING - {remaining//1000}s left)"
    else:
        status += " (LOCKED)"
    
    print(f"  Status: {status}")
    return selecting_mode

# Main test loop
print("Starting test loop... Press Ctrl+C to stop")
print()

try:
    while True:
        test_touch_handling()
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nTest stopped by user") 