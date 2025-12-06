from machine import Pin, SPI, PWM, UART
import gc9a01py as gc9a01
import utime as time  # Use utime for MicroPython compatibility
from fonts import NotoSans_32 as font
from fonts import NotoSans_64 as pmfont
from fram import read_filter_percent_fram, write_filter_percent_fram
try:
    from fonts import NotoSans_64 as bigfont
except ImportError:
    try:
        from fonts import NotoSans_48 as bigfont
    except ImportError:
        bigfont = font

# ==== Pin Assignments ====
# Display
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

# Fan/Motor
PWM_PIN = 4
BR_PIN = 5
FR_PIN = 6
FG_PIN = 7

def set_speed(percent):
    global filter_percent, current_motor_speed
    percent = max(0, min(100, percent))
    duty = int(((100 - percent) / 100) * 65535)
    pwm.duty_u16(duty)
    
    # Store current speed for filter tracking
    current_motor_speed = percent
    print(f"[DEBUG] Motor speed set to: {current_motor_speed}%")

pwm = PWM(Pin(PWM_PIN))
pwm.freq(25000)
set_speed(0)  # Set fan speed to 0 at startup to prevent unwanted spinning
brake = Pin(BR_PIN, Pin.OUT)
direction = Pin(FR_PIN, Pin.OUT)
fg = Pin(FG_PIN, Pin.IN)

# Buttons
TOUCH_PIN = 2  # GP2 for touch
RESET_PIN = 3
FILTER_SWITCH_PIN = 8
touch_pin = Pin(TOUCH_PIN, Pin.IN, Pin.PULL_UP)
reset_pin = Pin(RESET_PIN, Pin.IN, Pin.PULL_UP)
filter_switch = Pin(FILTER_SWITCH_PIN, Pin.IN, Pin.PULL_UP)

# Sensor (UART0)
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

# ==== Constants ====
ICON_W = 128
ICON_H = 128
ICON_Y = (tft.height - ICON_H) // 2  # Centered vertically
TEXT_Y = ICON_Y + ICON_H + 16
MODES = ["low", "medium", "high", "automatic"]
MODE_ICONS = {
    "low": "low.raw",
    "medium": "medium.raw",
    "high": "high.raw",
    "automatic": "automatic.raw"
}
MODE_SPEEDS = {
    "low": 30,
    "medium": 50,
    "high": 60,
    "max": 75
}

# ==== State ====
mode_idx = 0
filter_percent = 0
current_motor_speed = 0
target_motor_speed = 0  # The speed we want to run at (based on locked mode)
last_filter_increment = 0
FILTER_INCREMENT_INTERVAL = 1000  # 1 second between increments
last_touch = 1  # Start as released (PULL_UP)
last_reset = 1
TOUCH_DEBOUNCE_MS = 200
last_touch_time = 0
# Add a flag to force immediate redraw after mode changes
force_pm25_redraw = False
# Sleep mode state
sleep_mode = False
touch_hold_start = None
TOUCH_SLEEP_HOLD_TIME = 3000  # 3 seconds for sleep mode
# Mode selection state - simplified
mode_locked = False  # True when mode is locked in after 3 seconds
mode_selection_start = None
MODE_SELECTION_TIMEOUT = 3000  # 3 seconds to lock in mode

# ==== Helper Functions ====
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

def set_direction(forward=True):
    direction.value(1 if forward else 0)

def set_brake(on=False):
    brake.value(1 if on else 0)

def read_filter_percent():
    global filter_percent
    try:
        filter_percent = read_filter_percent_fram()
        return filter_percent
    except Exception as e:
        print(f"Error reading from FRAM: {e}")
        # Initialize to 0 if read fails
        filter_percent = 0.0
        write_filter_percent_fram(0.0)
        return filter_percent

def write_filter_percent(val):
    try:
        success = write_filter_percent_fram(val)
        if not success:
            print("FRAM write failed")
            return False
        return True
    except Exception as e:
        print(f"Error writing to FRAM: {e}")
        return False

def wait_for_filter_reset():
    """Wait for reset button to be held for 3 seconds to reset filter"""
    print("[INFO] Filter at 100% - waiting for reset button to be held for 3 seconds")
    
    # Stop motor and show reset screen
    set_speed(0)
    set_brake(True)
    
    tft.fill(gc9a01.BLACK)
    show_icon("filter_warning.raw")
    show_centered_text("Filter Full!", TEXT_Y)
    show_centered_text("Hold Reset 3s", TEXT_Y + 40)
    
    reset_start_time = None
    reset_held = False
    
    while not reset_held:
        # Check if reset button is pressed
        if reset_pin.value() == 0:  # Button pressed (active low)
            if reset_start_time is None:
                reset_start_time = time.ticks_ms()
                print("[DEBUG] Reset button pressed, starting timer")
        else:
            # Button released, reset timer
            if reset_start_time is not None:
                print("[DEBUG] Reset button released, resetting timer")
                reset_start_time = None
        
        # Check if button has been held for 3 seconds
        if reset_start_time is not None:
            hold_time = time.ticks_diff(time.ticks_ms(), reset_start_time)
            if hold_time >= 3000:  # 3 seconds
                reset_held = True
                print("[INFO] Reset button held for 3 seconds - resetting filter")
        
        time.sleep(0.1)

    # Reset filter percentage
    write_filter_percent(0.0)
    global filter_percent
    filter_percent = 0.0
    
    # Show reset confirmation
    tft.fill(gc9a01.BLACK)
    show_icon("filter.raw")
    show_centered_text("Filter Reset!", TEXT_Y)
    show_centered_text("0.00%", TEXT_Y + 40)
    time.sleep(2)
    
    # Resume normal operation
    set_brake(False)
    print("[INFO] Filter reset complete, resuming normal operation")

def read_sensor():
    pm1 = pm25 = pm10 = None
    tries = 0
    while tries < 5:
        available = uart.any()
        print(f"[DEBUG] UART available: {available}")
        if available >= 32:
            data = uart.read(32)
            print(f"[DEBUG] UART data: {data}")
            if data and len(data) == 32 and data[0] == 0x42 and data[1] == 0x4d:
                pm1 = data[10] << 8 | data[11]
                pm25 = data[12] << 8 | data[13]
                pm10 = data[14] << 8 | data[15]
                break
        tries += 1
    return pm1, pm25, pm10

def debounce(pin, last, delay=300):
    now = time.ticks_ms()
    try:
        diff = time.ticks_diff(now, last)
    except AttributeError:
        diff = now - last  # fallback for non-MicroPython
    if pin.value() == 0 and diff > delay:
        return now
    return last

def draw_scaled_text(font, text, x, y, color, scale=2):
    print(f"[DEBUG] Drawing scaled text: '{text}' at ({x},{y}) scale={scale}")
    for i, char in enumerate(text):
        char_code = ord(char)
        print(f"[DEBUG] Char '{char}' code {char_code} in font: {char_code in font.FONT}")
        try:
            char_bitmap = font.FONT[char_code]
        except (AttributeError, KeyError, IndexError):
            continue  # Skip unknown chars
        char_w = font.WIDTH
        char_h = font.HEIGHT
        # If char_bitmap is an int, treat as a single row
        if isinstance(char_bitmap, int):
            char_bitmap = [char_bitmap]
        for row in range(len(char_bitmap)):
            row_bits = char_bitmap[row]
            for col in range(char_w):
                if row_bits & (1 << (char_w - 1 - col)):
                    for dy in range(scale):
                        for dx in range(scale):
                            tft.pixel(x + i * char_w * scale + col * scale + dx, y + row * scale + dy, color)

def show_status(mode, pm1, pm25, pm10, filter_percent, last_drawn, pm25_display=None, selecting_mode=False):
    redraw = False
    # Mode selection: show normal icon centered
    if selecting_mode:
        if last_drawn is None or last_drawn[0] != mode or last_drawn[2] != 'selecting':
            tft.fill(gc9a01.BLACK)
            show_icon(MODE_ICONS.get(str(mode), "low.raw"))
            redraw = True
        return (mode, None, 'selecting'), redraw
    # After mode is locked in: show 64x64 icon and big PM2.5 value
    else:
        # Only redraw icon if mode changes or not in 'locked' state
        ICON_W = 64
        ICON_H = 64
        icon_y = (tft.height - ICON_H) // 2 - 30  # Always define icon_y
        if last_drawn is None or last_drawn[0] != mode or last_drawn[2] != 'locked':
            tft.fill(gc9a01.BLACK)
            # Draw 64x64 icon a bit higher than center
            try:
                with open(MODE_ICONS.get(str(mode), "low.raw"), "rb") as f:
                    buf = f.read()
                # If the icon is 128x128, scale down to 64x64 using nearest-neighbor (step=2)
                # For best quality, use pre-generated 64x64 icons
                if len(buf) == 128*128*2:
                    small_buf = bytearray()
                    for y in range(0, 128, 2):
                        for x in range(0, 128, 2):
                            i = (y * 128 + x) * 2
                            small_buf += buf[i:i+2]
                    buf = small_buf
                x = (tft.width - ICON_W) // 2
                tft.blit_buffer(buf, x, icon_y, ICON_W, ICON_H)
            except Exception as e:
                print("Error loading icon:", e)
            redraw = True
        # Only update PM2.5 value if it's provided (meaning it changed or needs redraw)
        if pm25_display is not None:
            pm25_text = f"{int(pm25_display):03d}"
            print(f"[DEBUG] Drawing PM2.5: {pm25_text}")
            # Smooth color gradient: green (0) -> yellow (50) -> orange (100) -> red (200+)
            def lerp(a, b, t):
                return int(a + (b - a) * t)
            pm = pm25_display
            if pm <= 50:
                # Green to Yellow
                t = pm / 50
                r = lerp(0, 255, t)
                g = 255
                b = 0
            elif pm <= 100:
                # Yellow to Orange
                t = (pm - 50) / 50
                r = 255
                g = lerp(255, 165, t)
                b = 0
            elif pm <= 200:
                # Orange to Red
                t = (pm - 100) / 100
                r = 255
                g = lerp(165, 0, t)
                b = 0
            else:
                r, g, b = 255, 0, 0
            pm_color = gc9a01.color565(r, g, b)
            w = tft.write_width(pmfont, pm25_text)
            x = (tft.width - w) // 2
            y = tft.height - pmfont.HEIGHT - 40
            tft.fill_rect(0, y, tft.width, pmfont.HEIGHT, gc9a01.BLACK)
            tft.write(pmfont, pm25_text, x, y, pm_color)
            print(f"[DEBUG] PM2.5 drawn at ({x}, {y}) with color {pm_color}")
        else:
            print(f"[DEBUG] No PM2.5 to display (pm25_display is None)")
        

        
        return (mode, pm25_display, 'locked'), redraw

def enter_sleep_mode():
    """Enter sleep mode - turn off motor and display"""
    global sleep_mode, current_motor_speed
    print("[INFO] Entering sleep mode")
    sleep_mode = True
    
    # Turn off motor
    set_speed(0)
    set_brake(True)
    current_motor_speed = 0
    
    # Turn off display backlight
    tft.backlight(False)
    
    print("[INFO] Sleep mode activated - motor and display off")

def exit_sleep_mode():
    """Exit sleep mode - restore motor and display"""
    global sleep_mode
    print("[INFO] Exiting sleep mode")
    sleep_mode = False
    
    # Turn on display backlight
    tft.backlight(True)
    tft.fill(gc9a01.BLACK)
    
    # Resume normal operation
    set_brake(False)
    print("[INFO] Sleep mode deactivated - resuming normal operation")

def wait_for_filter():
    print("[INFO] Waiting for filter...")
    set_speed(0)
    set_brake(True)
    if filter_switch.value():
        tft.fill(gc9a01.BLACK)
        show_icon("no_filter.raw")
        while filter_switch.value():
            time.sleep(0.1)
    print("[INFO] Filter inserted.")
    tft.fill(gc9a01.BLACK)  # Clear the no_filter image
    # Force redraw of locked-in state (small icon + PM2.5 value)
    global last_drawn, pm25
    # Use 0 for pm1, pm10, filter_percent if not available
    last_drawn, _ = show_status(MODES[mode_idx], 0, pm25 if 'pm25' in globals() else 0, 0, 0, None, pm25_display=pm25 if 'pm25' in globals() else 0, selecting_mode=False)
    set_brake(False)
    # Restore motor speed to target speed after filter is inserted
    set_speed(target_motor_speed)
    print(f"[INFO] Motor speed restored to {target_motor_speed}% after filter insertion")

# ==== Main Loop ====
set_brake(False)
set_direction(True)
read_filter_percent()
wait_for_filter()

splash_shown = True  # Skip splash, boot.py handles it

print("[INFO] Starting main loop.")
print(f"[DEBUG] Initial motor speed: {current_motor_speed}%")
print(f"[DEBUG] Initial filter usage: {filter_percent:.2f}%")
# Initialize mode selection timer - start counting down to lock in current mode
mode_selection_start = time.ticks_ms()
print(f"[INFO] Starting mode selection timer for: {MODES[mode_idx]}")

# Initialize target motor speed to the current mode's speed
target_motor_speed = MODE_SPEEDS[MODES[mode_idx]]
print(f"[INFO] Initial target motor speed set to: {target_motor_speed}% for mode: {MODES[mode_idx]}")

# Start the motor immediately at the target speed
set_speed(target_motor_speed)
print(f"[INFO] Motor started at {target_motor_speed}%")

last_drawn = None
pm25_last_display = None
pm25_display_time = 0
last_sensor_read = 0
pm1 = pm25 = pm10 = None
try:
    while True:
        print("[DEBUG] Loop iteration start.")
        print(f"[DEBUG] Current state - Mode: {MODES[mode_idx]}, Locked: {mode_locked}, Sleep: {sleep_mode}")
        filter_percent = read_filter_percent()
        print(f"[DEBUG] Current filter usage: {filter_percent:.2f}%")
        now = time.ticks_ms()

        # Increment filter usage based on motor speed every 1 second
        if time.ticks_diff(now, last_filter_increment) > FILTER_INCREMENT_INTERVAL:
            print(f"[DEBUG] Checking filter increment - current_motor_speed: {current_motor_speed}%")
            if current_motor_speed > 0:  # Only increment if motor is running
                increment = current_motor_speed / 30.0
                filter_percent += increment
                # Cap at 100%
                if filter_percent > 100.0:
                    filter_percent = 100.0
                # Save to FRAM
                write_filter_percent(filter_percent)
                print(f"[DEBUG] Filter increment: +{increment:.2f}% (motor speed: {current_motor_speed}%), New total: {filter_percent:.2f}%")
            else:
                print(f"[DEBUG] Motor not running (speed: {current_motor_speed}%), skipping filter increment")
            last_filter_increment = now
        
        if time.ticks_diff(now, last_sensor_read) > 1000:
            pm1, pm25, pm10 = read_sensor()
            last_sensor_read = now
            if pm25 is not None:
                print(f"[DEBUG] ✓ Sensor reading: PM2.5={pm25}")
            else:
                print(f"[DEBUG] ✗ No sensor data available")
        print(f"[DEBUG] Current sensor values: PM1={pm1}, PM2.5={pm25}, PM10={pm10}")

        # --- Touch handling for mode selection and sleep mode ---
        current_touch = touch_pin.value()
        print(f"[DEBUG] Touch pin value: {current_touch}")
        
        # Handle touch press (rising edge - touch sends 3.3V when pressed)
        if last_touch == 0 and current_touch == 1 and time.ticks_diff(now, last_touch_time) > TOUCH_DEBOUNCE_MS:
            print(f"[DEBUG] Touch rising edge detected at {now} ms (debounced)")
            touch_hold_start = now
            last_touch_time = now
        
        # Check for sleep mode during continuous hold
        elif last_touch == 1 and current_touch == 1 and touch_hold_start is not None:
            hold_time = time.ticks_diff(now, touch_hold_start)
            if hold_time >= TOUCH_SLEEP_HOLD_TIME and not sleep_mode:
                print(f"[DEBUG] Touch held for {hold_time}ms - entering sleep mode")
                enter_sleep_mode()
                touch_hold_start = None
        
        # Handle touch release (falling edge)
        elif last_touch == 1 and current_touch == 0:
            if touch_hold_start is not None:
                hold_time = time.ticks_diff(now, touch_hold_start)
                print(f"[DEBUG] Touch released after {hold_time}ms")
                
                if hold_time >= TOUCH_SLEEP_HOLD_TIME:
                    # Long press - toggle sleep mode (if not already entered during hold)
                    if sleep_mode:
                        exit_sleep_mode()
                else:
                    # Short press - handle mode selection or wake up from sleep
                    if sleep_mode:
                        # In sleep mode - single tap wakes up
                        print(f"[INFO] Single tap detected in sleep mode - waking up")
                        exit_sleep_mode()
                    else:
                        # Not in sleep mode - handle mode selection
                        if not mode_locked: # Only cycle if mode is not locked
                            mode_idx = (mode_idx + 1) % len(MODES)
                            mode_selection_start = now
                            print(f"[INFO] Touch cycle to next mode: {MODES[mode_idx]}")
                            force_pm25_redraw = True
                        else:
                            # Mode is locked - unlock it and start selection mode
                            mode_locked = False
                            mode_selection_start = now
                            print(f"[INFO] Mode unlocked - starting selection mode for: {MODES[mode_idx]}")
                            force_pm25_redraw = True
                
                touch_hold_start = None
        
        last_touch = current_touch
        
        # Check if mode selection timeout has expired
        if mode_selection_start is not None:
            if time.ticks_diff(now, mode_selection_start) >= MODE_SELECTION_TIMEOUT:
                # Timeout - lock in the current mode
                mode_locked = True
                mode_selection_start = None
                print(f"[INFO] Mode selection timeout - locking in: {MODES[mode_idx]}")
                print(f"[DEBUG] Mode locked: {mode_locked}, Mode: {MODES[mode_idx]}")
                force_pm25_redraw = True

        # --- Reset button handling ---
        current_reset = reset_pin.value()
        
        # Handle reset button press with better debouncing
        if last_reset == 1 and current_reset == 0:  # Just pressed
            print("[DEBUG] Reset button pressed")
            time.sleep(0.05)  # Small debounce delay
            
            if filter_percent < 100.0:
                # Quick reset for filter < 100%
                write_filter_percent(0.0)
                filter_percent = 0.0
                print("[INFO] Filter percent reset to 0.00%.")
                time.sleep(0.2)
            else:
                # For filter at 100%, start 3-second hold timer
                print("[DEBUG] Reset button pressed with filter at 100% - starting 3-second hold timer")
                reset_hold_start = time.ticks_ms()
                reset_holding = True
                
                # Wait for button release or 3-second hold
                while reset_pin.value() == 0:  # Button still pressed
                    hold_time = time.ticks_diff(time.ticks_ms(), reset_hold_start)
                    print(f"[DEBUG] Reset button hold time: {hold_time}ms")
                    if hold_time >= 3000:  # 3 seconds
                        # Reset filter
                        write_filter_percent(0.0)
                        filter_percent = 0.0
                        print("[INFO] Reset button held for 3 seconds - filter reset to 0.00%")
                        
                        # Show reset confirmation
                        tft.fill(gc9a01.BLACK)
                        show_icon("filter.raw")
                        show_centered_text("Filter Reset!", TEXT_Y)
                        show_centered_text("0.00%", TEXT_Y + 40)
                        time.sleep(2)
                        
                # Wait for button release if not already released
                while reset_pin.value() == 0:
                    time.sleep(0.1)

                # Wait for button release if not already released
                while reset_pin.value() == 0:
                    time.sleep(0.1)
                    
        last_reset = current_reset

        if filter_switch.value():
            wait_for_filter()
            continue

        # Skip normal operation if in sleep mode
        if sleep_mode:
            print("[DEBUG] In sleep mode - skipping normal operation")
            time.sleep(0.1)
            continue

        # Set fan speed based on current mode
        # Always run motor at target speed (whether mode is locked or not)
        if mode_locked:
            # Mode is locked - calculate new target speed based on current mode
            mode = MODES[mode_idx]
            if mode == "automatic":
                if pm25 is not None:
                    if pm25 <= 12:
                        target_motor_speed = MODE_SPEEDS["low"]
                        print("[INFO] Target speed set to LOW (auto)")
                    elif pm25 <= 35:
                        target_motor_speed = MODE_SPEEDS["medium"]
                        print("[INFO] Target speed set to MEDIUM (auto)")
                    elif pm25 <= 55:
                        target_motor_speed = MODE_SPEEDS["high"]
                        print("[INFO] Target speed set to HIGH (auto)")
                    else:
                        target_motor_speed = MODE_SPEEDS["max"]
                        print("[INFO] Target speed set to MAX (auto)")
                else:
                    target_motor_speed = MODE_SPEEDS["low"]
                    print("[INFO] Target speed set to LOW (auto, no sensor)")
            else:
                target_motor_speed = MODE_SPEEDS[mode]
                print(f"[INFO] Target speed set to {mode.upper()} (manual)")
            
            # Apply the target speed to motor
            set_speed(target_motor_speed)
            print(f"[DEBUG] Mode locked - motor speed set to: {current_motor_speed}%")
        else:
            # Mode not locked - keep running at current target speed
            set_speed(target_motor_speed)
            print(f"[DEBUG] Mode not locked - motor running at target speed: {current_motor_speed}%")

        # Only redraw if needed and not in sleep mode
        pm25_to_display = None
        now = time.ticks_ms()
        if not sleep_mode:
            # Show PM2.5 value only when it changes by ±2 or more, or every 2 seconds
            time_since_last_display = time.ticks_diff(now, pm25_display_time) if pm25_display_time > 0 else 9999
            value_change = abs(pm25 - pm25_last_display) if pm25 is not None and pm25_last_display is not None else 0
            
            print(f"[DEBUG] PM2.5 display check - time_since_last: {time_since_last_display}ms, value_change: {value_change}, force_redraw: {force_pm25_redraw}")
            
            if force_pm25_redraw or (pm25 is not None and (time_since_last_display > 2000 or pm25_last_display is None or value_change >= 2)):
                pm25_to_display = pm25
                pm25_last_display = pm25
                pm25_display_time = now
                force_pm25_redraw = False
                print(f"[DEBUG] Will display PM2.5: {pm25_to_display} (threshold: ±2)")
            else:
                print(f"[DEBUG] Skipping PM2.5 display - no significant change")
            last_drawn, did_redraw = show_status(MODES[mode_idx], pm1, pm25, pm10, filter_percent, last_drawn, pm25_to_display, selecting_mode=not mode_locked)
            if did_redraw:
                print(f"[DEBUG] Redrew icon for mode: {MODES[mode_idx]} (PM2.5: {pm25_to_display}, selecting: {mode_locked})")
        elif sleep_mode:
            # In sleep mode, don't update display
            print("[DEBUG] Sleep mode - skipping display updates")

        # Check if filter is at 100% and handle reset
        if filter_percent >= 100.0:
            wait_for_filter_reset()

        print("[DEBUG] Loop iteration end.\n")
        time.sleep(0.1)
finally:
    print("[INFO] Program exiting, stopping motor.")
    set_speed(0)
    set_brake(True)
