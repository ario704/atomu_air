from machine import Pin
import utime as time

# Setup touch pin
TOUCH_PIN = 2
touch_pin = Pin(TOUCH_PIN, Pin.IN, Pin.PULL_UP)

print("Touch Debug Test")
print("================")
print(f"Touch pin: GPIO{TOUCH_PIN}")
print(f"Initial touch value: {touch_pin.value()}")
print("Touch the button and watch the values...")
print("Press Ctrl+C to exit")
print()

last_touch = touch_pin.value()
touch_count = 0

try:
    while True:
        current_touch = touch_pin.value()
        
        # Detect touch press (rising edge)
        if last_touch == 0 and current_touch == 1:
            touch_count += 1
            print(f"[{time.ticks_ms()}] TOUCH PRESSED! (count: {touch_count})")
        
        # Detect touch release (falling edge)
        elif last_touch == 1 and current_touch == 0:
            print(f"[{time.ticks_ms()}] Touch released")
        
        # Show continuous values every 2 seconds
        if touch_count % 20 == 0 and touch_count > 0:
            print(f"[{time.ticks_ms()}] Current touch value: {current_touch}")
        
        last_touch = current_touch
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("\nTest completed.")
    print(f"Total touches detected: {touch_count}") 