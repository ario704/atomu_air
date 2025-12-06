from machine import Pin
import time

# === Corrected Pin Assignments ===
touch_pin = Pin(2, Pin.IN, Pin.PULL_UP)     # Touch (inverted logic)
reset_pin = Pin(3, Pin.IN, Pin.PULL_UP)     # Filter reset button
filter_switch = Pin(8, Pin.IN, Pin.PULL_UP) # Microswitch on GP8

# === Inverted logic for touch (0 = not pressed) ===
def touch_status():
    return "PRESSED" if touch_pin.value() == 1 else "RELEASED"

def button_status(pin):
    return "PRESSED" if pin.value() == 0 else "RELEASED"

def filter_present():
    return "YES" if filter_switch.value() == 0 else "NO"

print("Monitoring inputs (GP2/3/8)...")
time.sleep(1)

while True:
    print(
        "Touch: {:9} | Reset: {:9} | Filter Present: {:9}".format(
            touch_status(),
            button_status(reset_pin),
            filter_present()
        )
    )
    time.sleep(0.2)
