from machine import Pin, SPI
import gc9a01py as gc9a01
import utime as time
from fonts import NotoSans_32 as font

# Setup display
spi = SPI(1, baudrate=60000000, sck=Pin(10), mosi=Pin(11))
tft = gc9a01.GC9A01(
    spi,
    dc=Pin(13, Pin.OUT),
    cs=Pin(14, Pin.OUT),
    reset=Pin(12, Pin.OUT),
    backlight=Pin(15, Pin.OUT),
    rotation=0
)

tft.backlight(True)
tft.fill(gc9a01.BLACK)

# Setup touch pin
TOUCH_PIN = 2
touch_pin = Pin(TOUCH_PIN, Pin.IN, Pin.PULL_UP)

# Constants
MODES = ["low", "medium", "high", "automatic"]
MODE_ICONS = {
    "low": "low.raw",
    "medium": "medium.raw", 
    "high": "high.raw",
    "automatic": "automatic.raw"
}

ICON_W = 128
ICON_H = 128
ICON_Y = (tft.height - ICON_H) // 2

def show_icon(filename):
    try:
        with open(filename, "rb") as f:
            buf = f.read()
        x = (tft.width - ICON_W) // 2
        tft.blit_buffer(buf, x, ICON_Y, ICON_W, ICON_H)
    except Exception as e:
        print("Error loading icon:", filename, e)

def show_centered_text(text, y, color=gc9a01.WHITE):
    w = tft.write_width(font, text)
    x = (tft.width - w) // 2
    tft.write(font, text, x, y, color)

# Test variables
mode_idx = 0
mode_locked = False
mode_selection_start = time.ticks_ms()
MODE_SELECTION_TIMEOUT = 3000  # 3 seconds
last_touch = touch_pin.value()
last_touch_time = 0
TOUCH_DEBOUNCE_MS = 200

print("Touch Mode Test")
print("===============")
print(f"Current mode: {MODES[mode_idx]}")
print("Touch to cycle through modes")
print("Mode will lock after 3 seconds")
print()

# Show initial mode
tft.fill(gc9a01.BLACK)
show_icon(MODE_ICONS[MODES[mode_idx]])
show_centered_text(f"Mode: {MODES[mode_idx]}", ICON_Y + ICON_H + 20)
if not mode_locked:
    show_centered_text("(Selecting)", ICON_Y + ICON_H + 50, gc9a01.YELLOW)
else:
    show_centered_text("(Locked)", ICON_Y + ICON_H + 50, gc9a01.GREEN)

try:
    while True:
        now = time.ticks_ms()
        current_touch = touch_pin.value()
        
        # Handle touch press (rising edge)
        if last_touch == 0 and current_touch == 1 and time.ticks_diff(now, last_touch_time) > TOUCH_DEBOUNCE_MS:
            print(f"[{now}] Touch pressed")
            last_touch_time = now
        
        # Handle touch release (falling edge)
        elif last_touch == 1 and current_touch == 0:
            print(f"[{now}] Touch released")
            
            if not mode_locked:
                # Cycle to next mode
                mode_idx = (mode_idx + 1) % len(MODES)
                mode_selection_start = now
                print(f"[INFO] Mode changed to: {MODES[mode_idx]}")
                
                # Update display
                tft.fill(gc9a01.BLACK)
                show_icon(MODE_ICONS[MODES[mode_idx]])
                show_centered_text(f"Mode: {MODES[mode_idx]}", ICON_Y + ICON_H + 20)
                show_centered_text("(Selecting)", ICON_Y + ICON_H + 50, gc9a01.YELLOW)
            else:
                # Unlock mode and start selection
                mode_locked = False
                mode_selection_start = now
                print(f"[INFO] Mode unlocked - starting selection for: {MODES[mode_idx]}")
                
                # Update display
                tft.fill(gc9a01.BLACK)
                show_icon(MODE_ICONS[MODES[mode_idx]])
                show_centered_text(f"Mode: {MODES[mode_idx]}", ICON_Y + ICON_H + 20)
                show_centered_text("(Selecting)", ICON_Y + ICON_H + 50, gc9a01.YELLOW)
        
        last_touch = current_touch
        
        # Check if mode selection timeout has expired
        if mode_selection_start is not None and not mode_locked:
            if time.ticks_diff(now, mode_selection_start) >= MODE_SELECTION_TIMEOUT:
                # Timeout - lock in the current mode
                mode_locked = True
                mode_selection_start = None
                print(f"[INFO] Mode locked: {MODES[mode_idx]}")
                
                # Update display to show locked state
                tft.fill(gc9a01.BLACK)
                show_icon(MODE_ICONS[MODES[mode_idx]])
                show_centered_text(f"Mode: {MODES[mode_idx]}", ICON_Y + ICON_H + 20)
                show_centered_text("(Locked)", ICON_Y + ICON_H + 50, gc9a01.GREEN)
        
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("\nTest completed.") 