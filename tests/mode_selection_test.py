"""
Test script for the new simplified mode selection system.

Expected behavior:
1. Device starts showing current mode (e.g., "low")
2. Touch cycles to next mode immediately (low -> medium -> high -> auto -> low...)
3. If no touch for 3 seconds, mode locks in
4. Motor only runs after mode is locked in
"""

from machine import Pin
import utime as time

# Simulate the touch pin
TOUCH_PIN = 2
touch_pin = Pin(TOUCH_PIN, Pin.IN, Pin.PULL_UP)

# Mode configuration
MODES = ["low", "medium", "high", "automatic"]
MODE_SPEEDS = {
    "low": 30,
    "medium": 50,
    "high": 60,
    "max": 75
}

# State variables
mode_idx = 0
mode_locked = False
mode_selection_start = None
MODE_SELECTION_TIMEOUT = 3000  # 3 seconds
last_touch = 1  # Start as released (PULL_UP)
TOUCH_DEBOUNCE_MS = 200
last_touch_time = 0

def simulate_motor_speed(mode):
    """Simulate setting motor speed"""
    if mode == "automatic":
        return "AUTO (sensor-based)"
    else:
        return f"{MODE_SPEEDS[mode]}%"

def test_mode_selection():
    global mode_idx, mode_locked, mode_selection_start, last_touch, last_touch_time
    
    print("=== Mode Selection Test ===")
    print(f"Starting with mode: {MODES[mode_idx]}")
    print("Touch behavior: cycle to next mode")
    print("Timeout: 3 seconds to lock in mode")
    print("Motor: only runs after mode is locked")
    print()
    
    # Initialize timer
    mode_selection_start = time.ticks_ms()
    print(f"[START] Mode selection timer started for: {MODES[mode_idx]}")
    print(f"[MOTOR] Status: STOPPED (mode not locked yet)")
    print()
    
    test_duration = 10000  # 10 seconds test
    start_time = time.ticks_ms()
    
    while time.ticks_diff(time.ticks_ms(), start_time) < test_duration:
        now = time.ticks_ms()
        current_touch = touch_pin.value()
        
        # Handle touch press (rising edge)
        if last_touch == 0 and current_touch == 1 and time.ticks_diff(now, last_touch_time) > TOUCH_DEBOUNCE_MS:
            print(f"[TOUCH] Pressed at {time.ticks_diff(now, start_time)}ms")
            last_touch_time = now
        
        # Handle touch release (falling edge)
        elif last_touch == 1 and current_touch == 0:
            if not mode_locked:
                # Cycle to next mode
                mode_idx = (mode_idx + 1) % len(MODES)
                mode_selection_start = now
                print(f"[MODE] Cycled to: {MODES[mode_idx]}")
                print(f"[TIMER] Reset - 3 seconds to lock in")
                print(f"[MOTOR] Status: STOPPED (mode not locked yet)")
            else:
                print(f"[TOUCH] Released (mode already locked: {MODES[mode_idx]})")
        
        last_touch = current_touch
        
        # Check timeout
        if not mode_locked and mode_selection_start is not None:
            time_remaining = MODE_SELECTION_TIMEOUT - time.ticks_diff(now, mode_selection_start)
            if time_remaining <= 0:
                # Lock in the mode
                mode_locked = True
                mode_selection_start = None
                print(f"[LOCK] Mode locked in: {MODES[mode_idx]}")
                print(f"[MOTOR] Status: RUNNING at {simulate_motor_speed(MODES[mode_idx])}")
            elif time_remaining % 1000 < 100:  # Print every second
                print(f"[TIMER] {time_remaining//1000}s remaining to lock in {MODES[mode_idx]}")
        
        time.sleep(0.1)
    
    print()
    print("=== Test Complete ===")
    print(f"Final mode: {MODES[mode_idx]}")
    print(f"Mode locked: {mode_locked}")
    if mode_locked:
        print(f"Motor status: RUNNING at {simulate_motor_speed(MODES[mode_idx])}")
    else:
        print("Motor status: STOPPED (mode never locked)")

if __name__ == "__main__":
    test_mode_selection() 