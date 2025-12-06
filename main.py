from machine import Pin, SPI, PWM, UART, I2C
import gc9a01py as gc9a01
from fonts import NotoSans_32 as font
from fonts import NotoSans_64 as pmfont
from fram import init_fram
import gc
import utime as time

# Force garbage collection at start
gc.collect()

print("=== Initializing Atomu Air Purifier Components ===")

# 1. FRAM (I2C0 on GP16/GP17)
print("Initializing FRAM...")
if callable(init_fram):
    fram_success = init_fram()
else:
    raise Exception("init_fram is not callable. Check import.")
if fram_success:
    print("✓ FRAM initialized successfully")
else:
    print("✗ FRAM initialization failed")
    raise Exception("FRAM is required for operation")

# 2. Display (SPI1 on GP10/GP11)
print("Initializing Display...")
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
print("✓ Display initialized")

# 3. Motor/Fan (PWM on GP4, control pins on GP5/GP6/GP7)
print("Initializing Motor...")
PWM_PIN = 4
BR_PIN = 5  # Brake
FR_PIN = 6  # Forward/Reverse
FG_PIN = 7  # Fan feedback

pwm = PWM(Pin(PWM_PIN))
pwm.freq(25000)
pwm.duty_u16(0)  # Start with motor off

brake = Pin(BR_PIN, Pin.OUT)
direction = Pin(FR_PIN, Pin.OUT)
fg = Pin(FG_PIN, Pin.IN)

# Set initial motor state
brake.value(True)  # Release brake
direction.value(1)  # Forward direction
print("✓ Motor initialized")

# 4. Touch Module (GP2)
print("Initializing Touch Module...")
TOUCH_PIN = 2
touch_pin = Pin(TOUCH_PIN, Pin.IN, Pin.PULL_UP)
print("✓ Touch module initialized")

# 5. Filter Reset Button (GP3)
print("Initializing Filter Reset Button...")
RESET_PIN = 3
reset_pin = Pin(RESET_PIN, Pin.IN, Pin.PULL_UP)
print("✓ Filter reset button initialized")

# 6. Filter Micro Switch (GP8)
print("Initializing Filter Micro Switch...")
FILTER_SWITCH_PIN = 8
filter_switch = Pin(FILTER_SWITCH_PIN, Pin.IN, Pin.PULL_UP)
print("✓ Filter micro switch initialized")

# 7. PM2.5 Sensor (UART0 on GP0/GP1)
print("Initializing PM2.5 Sensor (UART0)...")
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
print("✓ PM2.5 sensor UART initialized")

# 8. Sensor 'set' pin (GP9)
print("Initializing Sensor 'set' Pin (GP9)...")
SENSOR_SET_PIN = 9
sensor_set_pin = Pin(SENSOR_SET_PIN, Pin.OUT)
sensor_set_pin.value(1)  # Power ON sensor by default
print("✓ Sensor 'set' pin initialized and set HIGH (sensor ON)")

# 9. Buzzer (GP18)
print("Initializing Buzzer...")
BUZZER_PIN = 18
buzzer = Pin(BUZZER_PIN, Pin.OUT)
buzzer.value(0)  # Start with buzzer off
print("✓ Buzzer initialized")

print("=== All Components Initialized ===")

# Startup buzz for 0.1 second
def buzz():
    buzzer.value(1)
    time.sleep(0.1)
    buzzer.value(0)

buzz()

# Startup beep for 0.05 second
def beep():
    buzzer.value(1)
    time.sleep(0.05)
    buzzer.value(0)

# === Placeholder functions ===
def sleep():
    beep()
    print("[INFO] Entering sleep mode...")
    gc.collect()  # Clear Pico memory
    brake.value(1)  # Set motor brake to true
    sensor_set_pin.value(0)  # Turn sensor off
    tft.backlight(False)  # Turn display off
    tft.fill(gc9a01.BLACK)  # Clear display contents
    print("[INFO] Device is now in sleep mode. Waiting for tap to wake...")
    last_touch = touch_pin.value()
    touch_press_time = None
    debounce_ms = 200
    last_event_time = 0
    tap_max = 1000  # 1 second
    while True:
        now = time.ticks_ms()
        current_touch = touch_pin.value()
        if time.ticks_diff(now, last_event_time) < debounce_ms:
            last_touch = current_touch
            time.sleep_ms(10)
            continue
        if last_touch == 0 and current_touch == 1:
            touch_press_time = now
            print("[DEBUG] Touch pressed in sleep")
        elif last_touch == 1 and current_touch == 0:
            if touch_press_time is not None:
                held_time = time.ticks_diff(now, touch_press_time)
                print(f"[DEBUG] Touch released in sleep after {held_time} ms")
                if held_time < tap_max:
                    print("[DEBUG] Tap detected in sleep: returning awake")
                    beep()
                    return awake
                touch_press_time = None
            last_event_time = now
        last_touch = current_touch
        time.sleep_ms(10)
    # Should never reach here
    return sleep

def awake():
    beep()
    brake.value(1)
    print("[INFO] Waking up...")
    sensor_set_pin.value(1)  # Power ON sensor
    tft.backlight(True)  # Turn on display backlight
    tft.fill(gc9a01.BLACK)
    gc.collect()  # Clear Pico memory
    try:
        gc.collect()
        with open("Atomu.raw", "rb") as f:
            logo_data = f.read()
        x = (tft.width - 200) // 2
        y = (tft.height - 200) // 2
        tft.blit_buffer(logo_data, x, y, 200, 200)
        del logo_data
        gc.collect()
        print("[INFO] Atomu logo displayed")
    except Exception as e:
        print(f"[WARN] Error loading Atomu logo: {e}")
        w = tft.write_width(font, "ATOMU")
        x = (tft.width - w) // 2
        y = (tft.height - 32) // 2
        tft.write(font, "ATOMU", x, y, gc9a01.WHITE)
        print("[INFO] Atomu text displayed (fallback)")
    print("[INFO] Listening for touch (tap/hold) and filter reset button...")
    last_touch = touch_pin.value()
    touch_press_time = None
    touch_hold_fired = False
    debounce_ms = 200
    last_touch_event_time = 0
    tap_max = 1000  # 1 second
    hold_min = 2000  # 2 seconds
    last_reset = reset_pin.value()
    reset_press_time = None
    reset_hold_fired = False
    last_reset_event_time = 0
    reset_hold_min = 3000  # 3 seconds
    while True:
        now = time.ticks_ms()
        current_touch = touch_pin.value()
        if time.ticks_diff(now, last_touch_event_time) >= debounce_ms:
            if last_touch == 0 and current_touch == 1:
                touch_press_time = now
                touch_hold_fired = False
                print("[DEBUG] Touch pressed in awake")
            elif last_touch == 1 and current_touch == 1 and touch_press_time is not None and not touch_hold_fired:
                held_time = time.ticks_diff(now, touch_press_time)
                if held_time >= hold_min:
                    print(f"[DEBUG] Hold detected in awake ({held_time} ms): returning sleep")
                    touch_hold_fired = True
                    last_touch_event_time = now
                    return sleep
            elif last_touch == 1 and current_touch == 0:
                if touch_press_time is not None and not touch_hold_fired:
                    held_time = time.ticks_diff(now, touch_press_time)
                    print(f"[DEBUG] Touch released in awake after {held_time} ms")
                    if held_time < tap_max:
                        print("[DEBUG] Tap detected in awake: returning filter_check")
                        return filter_check
                    touch_press_time = None
                last_touch_event_time = now
            last_touch = current_touch
        current_reset = reset_pin.value()
        if time.ticks_diff(now, last_reset_event_time) >= debounce_ms:
            if last_reset == 1 and current_reset == 0:
                reset_press_time = now
                reset_hold_fired = False
                print("[DEBUG] Filter reset button pressed in awake")
            elif last_reset == 0 and current_reset == 0 and reset_press_time is not None and not reset_hold_fired:
                held_time = time.ticks_diff(now, reset_press_time)
                if held_time >= reset_hold_min:
                    print(f"[DEBUG] Filter reset button held for {held_time} ms: returning filter_reset")
                    reset_hold_fired = True
                    last_reset_event_time = now
                    return filter_reset
            elif last_reset == 0 and current_reset == 1:
                reset_press_time = None
                reset_hold_fired = False
                last_reset_event_time = now
            last_reset = current_reset
        time.sleep_ms(10)
    return awake

def filter_check():
    print("[INFO] Checking filter...")
    gc.collect()  # Clear Pico memory
    if filter_switch.value():  # Not active (open/high)
        print("[DEBUG] Filter microswitch not active: returning no_filter")
        return no_filter
    beep()
    try:
        from fram import read_filter_percent_fram
        filter_percent = read_filter_percent_fram()
        print(f"[DEBUG] Filter percent read from FRAM: {filter_percent:.2f}%")
    except Exception as e:
        print(f"[WARN] Could not read filter percent from FRAM: {e}")
        filter_percent = 0.0
    if filter_percent < 85:
        image_file = "filter.raw"
    elif filter_percent < 100:
        image_file = "filter_warning.raw"
    else:
        image_file = "filter_full.raw"
    tft.fill(gc9a01.BLACK)
    try:
        gc.collect()
        with open(image_file, "rb") as f:
            img_data = f.read()
        img_w, img_h = 128, 128
        x = (tft.width - img_w) // 2
        y = (tft.height - img_h) // 2 - 30  # 30px above center
        tft.blit_buffer(img_data, x, y, img_w, img_h)
        del img_data
        gc.collect()
        print(f"[INFO] {image_file} displayed at ({x},{y})")
    except Exception as e:
        print(f"[WARN] Could not display {image_file}: {e}")
    percent_str = f"{int(filter_percent)}%"
    w = tft.write_width(font, percent_str)
    x = (tft.width - w) // 2
    y = tft.height - 70  # 70px from bottom (higher than before)
    tft.write(font, percent_str, x, y, gc9a01.WHITE)
    print(f"[INFO] Filter percent {percent_str} displayed at y={y}")
    time.sleep(3)
    if filter_switch.value():
        print("[DEBUG] Filter microswitch not active after wait: returning no_filter")
        return no_filter
    print("[INFO] Proceeding to mode_select()")
    return (mode_select, ("low",))

def no_filter():
    beep(); time.sleep(0.2); beep()
    print("[INFO] No filter detected. Entering no_filter state...")
    gc.collect()  # Clear Pico memory
    brake.value(1)  # Set motor brake to true
    tft.fill(gc9a01.BLACK)
    try:
        gc.collect()
        with open("no_filter.raw", "rb") as f:
            img_data = f.read()
        img_w, img_h = 128, 128
        x = (tft.width - img_w) // 2
        y = (tft.height - img_h) // 2
        tft.blit_buffer(img_data, x, y, img_w, img_h)
        del img_data
        gc.collect()
        print(f"[INFO] no_filter.raw displayed at ({x},{y})")
    except Exception as e:
        print(f"[WARN] Could not display no_filter.raw: {e}")
    print("[INFO] Waiting for filter to be inserted or touch hold (sleep)...")
    last_touch = touch_pin.value()
    touch_press_time = None
    touch_hold_fired = False
    debounce_ms = 200
    last_touch_event_time = 0
    tap_max = 1000  # 1 second
    hold_min = 2000  # 2 seconds
    while True:
        now = time.ticks_ms()
        if not filter_switch.value():
            print("[INFO] Filter detected. Proceeding to filter_check...")
            return filter_check
        current_touch = touch_pin.value()
        if time.ticks_diff(now, last_touch_event_time) >= debounce_ms:
            if last_touch == 0 and current_touch == 1:
                touch_press_time = now
                touch_hold_fired = False
                print("[DEBUG] Touch pressed in no_filter")
            elif last_touch == 1 and current_touch == 1 and touch_press_time is not None and not touch_hold_fired:
                held_time = time.ticks_diff(now, touch_press_time)
                if held_time >= hold_min:
                    print(f"[DEBUG] Hold detected in no_filter ({held_time} ms): returning sleep")
                    touch_hold_fired = True
                    return sleep
            elif last_touch == 1 and current_touch == 0:
                if touch_press_time is not None and not touch_hold_fired:
                    held_time = time.ticks_diff(now, touch_press_time)
                    if held_time < tap_max:
                        print(f"[DEBUG] Tap detected in no_filter after {held_time} ms (no action)")
                    touch_press_time = None
                touch_hold_fired = False
                last_touch_event_time = now
            last_touch = current_touch
        time.sleep_ms(10)
    return no_filter

def filter_reset():
    beep(); time.sleep(0.2); beep(); time.sleep(0.2); beep()
    print("[INFO] Filter reset state...")
    try:
        from fram import write_filter_percent_fram
        write_filter_percent_fram(0.0)
        print("[INFO] Filter percent reset to 0 in FRAM")
    except Exception as e:
        print(f"[WARN] Could not reset filter percent in FRAM: {e}")
    tft.fill(gc9a01.BLACK)
    try:
        gc.collect()
        with open("filter_reset.raw", "rb") as f:
            img_data = f.read()
        img_w, img_h = 128, 128
        x = (tft.width - img_w) // 2
        y = (tft.height - img_h) // 2
        tft.blit_buffer(img_data, x, y, img_w, img_h)
        del img_data
        gc.collect()
        print(f"[INFO] filter_reset.raw displayed at ({x},{y})")
    except Exception as e:
        print(f"[WARN] Could not display filter_reset.raw: {e}")
    print("[INFO] Waiting 3 seconds in filter_reset...")
    time.sleep(3)
    print("[INFO] Returning to awake() from filter_reset...")
    return awake

def mode_select(mode):
    print(f"[INFO] Mode select called with input: {mode}")
    modes = ["low", "med", "high", "auto"]
    if mode not in modes:
        print(f"[WARN] Invalid mode '{mode}', defaulting to 'low'")
        mode = "low"
    mode_idx = modes.index(mode)
    debounce_ms = 200
    tap_max = 1000  # 1 second
    while True:
        selected_mode = modes[mode_idx]
        tft.fill(gc9a01.BLACK)
        image_file = f"{selected_mode}.raw"
        try:
            gc.collect()
            with open(image_file, "rb") as f:
                img_data = f.read()
            img_w, img_h = 128, 128
            x = (tft.width - img_w) // 2
            y = (tft.height - img_h) // 2
            tft.blit_buffer(img_data, x, y, img_w, img_h)
            del img_data
            gc.collect()
            print(f"[INFO] {image_file} displayed at ({x},{y})")
        except Exception as e:
            print(f"[WARN] Could not display {image_file}: {e}")
        print(f"[INFO] Waiting for tap to change mode or timeout to lock in '{selected_mode}'...")
        last_touch = touch_pin.value()
        touch_press_time = None
        last_touch_event_time = 0
        tap_detected = False
        start_time = time.ticks_ms()
        while True:
            now = time.ticks_ms()
            if time.ticks_diff(now, start_time) > 3000:
                print(f"[INFO] Mode '{selected_mode}' locked in (timeout)")
                return (mode_activated, (selected_mode,))
            current_touch = touch_pin.value()
            if time.ticks_diff(now, last_touch_event_time) < debounce_ms:
                last_touch = current_touch
                time.sleep_ms(10)
                continue
            if last_touch == 0 and current_touch == 1:
                touch_press_time = now
            elif last_touch == 1 and current_touch == 0:
                if touch_press_time is not None:
                    held_time = time.ticks_diff(now, touch_press_time)
                    if held_time < tap_max:
                        print(f"[DEBUG] Tap detected in mode_select after {held_time} ms")
                        tap_detected = True
                        last_touch_event_time = now
                        break
                    touch_press_time = None
                last_touch_event_time = now
            last_touch = current_touch
            time.sleep_ms(10)
        if tap_detected:
            beep()
            mode_idx = (mode_idx + 1) % len(modes)
            print(f"[INFO] Cycling to next mode: {modes[mode_idx]}")
    return (mode_select, (modes[mode_idx],))

def mode_activated(mode):
    beep()
    print(f"[INFO] Mode activated: {mode}")
    modes = ["low", "med", "high", "auto"]
    if mode not in modes:
        print(f"[WARN] Invalid mode '{mode}', defaulting to 'low'")
        mode = "low"
    tft.fill(gc9a01.BLACK)
    brake.value(0)
    print("[INFO] Motor brake set to off")
    image_file = f"{mode}.raw"
    img_w, img_h = 128, 128
    scaled_w, scaled_h = 64, 64
    x = (tft.width - scaled_w) // 2
    y = (tft.height - scaled_h) // 2 - 40  # Move icon 10px higher (was -30)
    try:
        gc.collect()
        with open(image_file, "rb") as f:
            img_data = f.read()
        scaled_data = bytearray()
        for row in range(0, img_h, 2):
            for col in range(0, img_w, 2):
                orig_pos = (row * img_w + col) * 2
                if orig_pos + 1 < len(img_data):
                    scaled_data.append(img_data[orig_pos])
                    scaled_data.append(img_data[orig_pos + 1])
        tft.blit_buffer(scaled_data, x, y, scaled_w, scaled_h)
        del img_data
        del scaled_data
        gc.collect()
        print(f"[INFO] {image_file} scaled and displayed at ({x},{y})")
    except Exception as e:
        print(f"[WARN] Could not display scaled {image_file}: {e}")
    pm25_last = None
    pm25_x_center = tft.width // 2
    pm25_y = y + scaled_h + 30  # Move PM2.5 text 20px lower (was +10)
    # Define color constants
    PERSIAN_GREEN = gc9a01.color565(0, 166, 147)
    MEDIUM_ORANGE = gc9a01.color565(255, 153, 0)
    RED = gc9a01.RED
    pm25_color = PERSIAN_GREEN
    pm25_bg_color = gc9a01.BLACK
    def set_motor_speed(percent):
        percent = max(0, min(100, percent))
        duty = int(((100 - percent) / 100) * 65535)
        pwm.duty_u16(duty)
        print(f"[INFO] Motor speed set to {percent}% (duty {duty})")
    def get_pm25():
        if uart.any():
            try:
                data = uart.read()
                if data and len(data) >= 32:
                    pm25 = int.from_bytes(data[6:8], 'big')
                    return pm25
            except Exception as e:
                print(f"[WARN] Error reading PM2.5: {e}")
        return None
    if mode == "low":
        set_motor_speed(40)
    elif mode == "med":
        set_motor_speed(55)
    elif mode == "high":
        set_motor_speed(75)
    debounce_ms = 200
    tap_max = 1000
    hold_min = 2000
    reset_hold_min = 3000
    last_touch = touch_pin.value()
    touch_press_time = None
    touch_hold_fired = False
    last_touch_event_time = 0
    last_reset = reset_pin.value()
    reset_press_time = None
    reset_hold_fired = False
    last_reset_event_time = 0
    pm25_update_time = 0
    filter_increment_time = 0
    while True:
        now = time.ticks_ms()
        if filter_switch.value():
            print("[INFO] Filter microswitch not active: returning no_filter")
            return no_filter
        current_reset = reset_pin.value()
        if time.ticks_diff(now, last_reset_event_time) >= debounce_ms:
            if last_reset == 1 and current_reset == 0:
                reset_press_time = now
                reset_hold_fired = False
                print("[DEBUG] Filter reset button pressed in mode_activated")
            elif last_reset == 0 and current_reset == 0 and reset_press_time is not None and not reset_hold_fired:
                held_time = time.ticks_diff(now, reset_press_time)
                if held_time >= reset_hold_min:
                    print(f"[DEBUG] Filter reset button held for {held_time} ms: returning filter_reset")
                    reset_hold_fired = True
                    last_reset_event_time = now
                    return filter_reset
            elif last_reset == 0 and current_reset == 1:
                reset_press_time = None
                reset_hold_fired = False
                last_reset_event_time = now
            last_reset = current_reset
        current_touch = touch_pin.value()
        if time.ticks_diff(now, last_touch_event_time) >= debounce_ms:
            if last_touch == 0 and current_touch == 1:
                touch_press_time = now
                touch_hold_fired = False
                print("[DEBUG] Touch pressed in mode_activated")
            elif last_touch == 1 and current_touch == 1 and touch_press_time is not None and not touch_hold_fired:
                held_time = time.ticks_diff(now, touch_press_time)
                if held_time >= hold_min:
                    print(f"[DEBUG] Hold detected in mode_activated ({held_time} ms): returning sleep")
                    touch_hold_fired = True
                    last_touch_event_time = now
                    return sleep
            elif last_touch == 1 and current_touch == 0:
                if touch_press_time is not None and not touch_hold_fired:
                    held_time = time.ticks_diff(now, touch_press_time)
                    if held_time < tap_max:
                        print(f"[DEBUG] Tap detected in mode_activated: returning mode_select({mode})")
                        last_touch_event_time = now
                        return (mode_select, (mode,))
                    touch_press_time = None
                touch_hold_fired = False
                last_touch_event_time = now
            last_touch = current_touch
        if time.ticks_diff(now, pm25_update_time) > 500:
            pm25 = get_pm25()
            if pm25 is not None:
                if pm25_last is None or abs(pm25 - pm25_last) >= 2:
                    # Set color based on pm25 value
                    if pm25 <= 35:
                        pm25_color = PERSIAN_GREEN
                    elif pm25 <= 150:
                        pm25_color = MEDIUM_ORANGE
                    else:
                        pm25_color = RED
                    # Increase cleared area to prevent artifacts
                    tft.fill_rect(pm25_x_center - 70, pm25_y - 10, 140, 60, pm25_bg_color)
                    val_str = f"{pm25:03d}"
                    w = tft.write_width(pmfont, val_str)
                    x_val = pm25_x_center - w // 2
                    tft.write(pmfont, val_str, x_val, pm25_y, pm25_color)
                    print(f"[INFO] PM2.5 value updated: {pm25}")
                    pm25_last = pm25
                if mode == "auto":
                    if pm25 <= 35:
                        set_motor_speed(40)
                    elif pm25 <= 150:
                        set_motor_speed(55)
                    else:
                        set_motor_speed(75)
            pm25_update_time = now
        if time.ticks_diff(now, filter_increment_time) > 1000:
            try:
                from fram import read_filter_percent_fram, write_filter_percent_fram
                filter_percent = read_filter_percent_fram()
                current_duty = pwm.duty_u16()
                if current_duty == int(((100 - 35) / 100) * 65535):
                    increment = 0.5  # Still use 0.5 for 40% speed, or adjust if needed
                elif current_duty == int(((100 - 55) / 100) * 65535):
                    increment = 1.0
                elif current_duty == int(((100 - 75) / 100) * 65535):
                    increment = 1.5
                else:
                    percent = 100 - (current_duty / 65535) * 100
                    if percent < 45:
                        increment = 0.5
                    elif percent < 65:
                        increment = 1.0
                    else:
                        increment = 1.5
                new_value = min(100.0, filter_percent + increment)
                write_filter_percent_fram(new_value)
                print(f"[INFO] Filter percent incremented by {increment}, now {new_value:.2f}%")
            except Exception as e:
                print(f"[WARN] Could not increment filter percent: {e}")
            filter_increment_time = now
        time.sleep_ms(10)
    return (mode_activated, (mode,))

# --- Main state machine loop ---
def run_state_machine():
    state = sleep
    args = ()
    while True:
        result = state(*args)
        if isinstance(result, tuple):
            state, args = result[0], result[1]
        else:
            state, args = result, ()

run_state_machine()