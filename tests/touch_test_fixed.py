from machine import Pin
import utime as time

# Pin setup
TOUCH_PIN = 2
touch_pin = Pin(TOUCH_PIN, Pin.IN, Pin.PULL_UP)

# Constants
TOUCH_DEBOUNCE_MS = 200
TOUCH_SLEEP_HOLD_TIME = 5000  # 5 seconds for sleep mode

# State variables
last_touch = 1  # Start as released (PULL_UP)
last_touch_time = 0
touch_hold_start = None
sleep_mode = False

# Test modes
MODES = ["low", "medium", "high", "automatic"]
mode_idx = 0
selecting_mode = False
select_mode_time = 0
SELECT_MODE_TIMEOUT = 3000  # ms

print("=== Touch Test - Fixed Version ===")
print("Touch pin setup: HIGH when pressed, LOW when released")
print("Short press: Cycle through modes")
print("Long press (5s): Toggle sleep mode")
print("Current mode:", MODES[mode_idx])
print("Sleep mode:", sleep_mode)
print("=" * 40)

try:
    while True:
        now = time.ticks_ms()
        current_touch = touch_pin.value()
        
        # Handle touch press (rising edge - touch sends 3.3V when pressed)
        if last_touch == 0 and current_touch == 1 and time.ticks_diff(now, last_touch_time) > TOUCH_DEBOUNCE_MS:
            print(f"[{now}] Touch PRESSED (rising edge)")
            touch_hold_start = now
            last_touch_time = now
        
        # Handle touch release (falling edge)
        elif last_touch == 1 and current_touch == 0:
            if touch_hold_start is not None:
                hold_time = time.ticks_diff(now, touch_hold_start)
                print(f"[{now}] Touch RELEASED after {hold_time}ms")
                
                if hold_time >= TOUCH_SLEEP_HOLD_TIME:
                    # Long press - toggle sleep mode
                    if sleep_mode:
                        print(f"[{now}] EXITING SLEEP MODE")
                        sleep_mode = False
                    else:
                        print(f"[{now}] ENTERING SLEEP MODE")
                        sleep_mode = True
                else:
                    # Short press - cycle through modes (only if not in sleep mode)
                    if not sleep_mode:
                        if not selecting_mode:
                            selecting_mode = True
                            select_mode_time = now
                            print(f"[{now}] Entering mode selection. Current mode: {MODES[mode_idx]}")
                        else:
                            mode_idx = (mode_idx + 1) % len(MODES)
                            select_mode_time = now
                            print(f"[{now}] Mode changed to: {MODES[mode_idx]}")
                    else:
                        print(f"[{now}] Short press ignored (in sleep mode)")
                
                touch_hold_start = None
        
        # If in selection mode, check for timeout
        if selecting_mode:
            if time.ticks_diff(time.ticks_ms(), select_mode_time) > SELECT_MODE_TIMEOUT:
                selecting_mode = False
                print(f"[{now}] Mode locked in: {MODES[mode_idx]}")
        
        last_touch = current_touch
        
        # Show status every 2 seconds
        if now % 2000 < 100:  # Every 2 seconds
            status = f"Mode: {MODES[mode_idx]} | Sleep: {sleep_mode} | Touch: {current_touch}"
            if selecting_mode:
                status += " | SELECTING"
            print(f"[{now}] Status: {status}")
        
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nTest stopped by user")
except Exception as e:
    print(f"Error: {e}") 