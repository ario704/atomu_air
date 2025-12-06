from machine import Pin, SPI, PWM, UART, I2C
import gc9a01py as gc9a01
import utime as time
from fonts import NotoSans_32 as font
from fonts import NotoSans_64 as pmfont
from fram import init_fram, read_filter_percent_fram, write_filter_percent_fram
import gc

# Force garbage collection at start
gc.collect()

# ==== Component Initialization ====

# 1. FRAM (I2C0 on GP16/GP17)
print("Initializing FRAM...")
try:
    fram_success = init_fram()
    if fram_success:
        print("✓ FRAM initialized successfully")
    else:
        print("✗ FRAM initialization failed")
        raise Exception("FRAM is required for operation")
except Exception as e:
    print(f"✗ FRAM initialization error: {e}")
    raise

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
print("Initializing PM2.5 Sensor...")
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
print("✓ PM2.5 sensor initialized")

# 8. Buzzer (GP18)
print("Initializing Buzzer...")
BUZZER_PIN = 18
buzzer = Pin(BUZZER_PIN, Pin.OUT)
buzzer.value(0)  # Start with buzzer off
print("✓ Buzzer initialized")

print("=== All Components Initialized ===")

# Startup beep
buzzer.value(1)
time.sleep_ms(100)
buzzer.value(0)

# Wait for user tap to start
print("Waiting for user tap...")
TOUCH_DEBOUNCE_MS = 200
last_touch_time = 0

while True:
    current_touch = touch_pin.value()
    
    # Check for touch press (rising edge - touch sends 3.3V when pressed)
    if current_touch == 1:  # Touch detected
        now = time.ticks_ms()
        if time.ticks_diff(now, last_touch_time) > TOUCH_DEBOUNCE_MS:
            print("Touch detected - starting system")
            
            # Short beep
            buzzer.value(1)
            time.sleep_ms(50)
            buzzer.value(0)
            
            # Turn on screen and show ATOMU logo
            tft.backlight(True)
            tft.fill(gc9a01.BLACK)
            
            # Load and display ATOMU logo (200x200 pixels)
            try:
                gc.collect()  # Free memory before loading large logo
                with open("Atomu.raw", "rb") as f:
                    logo_data = f.read()
                # Center the 200x200 logo on the 240x240 display
                x = (tft.width - 200) // 2
                y = (tft.height - 200) // 2
                tft.blit_buffer(logo_data, x, y, 200, 200)
                print("ATOMU logo displayed")
                del logo_data  # Free memory immediately after display
                gc.collect()
            except Exception as e:
                print(f"Error loading ATOMU logo: {e}")
                # Fallback: show text if logo fails to load
                tft.fill(gc9a01.BLACK)
                w = tft.write_width(font, "ATOMU")
                x = (tft.width - w) // 2
                y = (tft.height - 32) // 2
                tft.write(font, "ATOMU", x, y, gc9a01.WHITE)
                print("ATOMU text displayed (fallback)")
            
            break  # Exit the wait loop
    
    time.sleep_ms(10)  # Small delay to prevent busy waiting

# Wait for second tap to check filter
print("Waiting for second tap to check filter...")
last_touch_time = 0

while True:
    current_touch = touch_pin.value()
    
    # Check for touch press (rising edge - touch sends 3.3V when pressed)
    if current_touch == 1:  # Touch detected
        now = time.ticks_ms()
        if time.ticks_diff(now, last_touch_time) > TOUCH_DEBOUNCE_MS:
            print("Second touch detected - checking filter...")
            
            # Short beep
            buzzer.value(1)
            time.sleep_ms(50)
            buzzer.value(0)
            
            # Check filter microswitch
            if filter_switch.value():  # No filter installed (switch is open/high)
                print("No filter detected")
                tft.fill(gc9a01.BLACK)
                
                # Show no_filter image
                try:
                    gc.collect()  # Free memory before loading image
                    with open("no_filter.raw", "rb") as f:
                        no_filter_data = f.read()
                    # Center the image on the display
                    x = (tft.width - 128) // 2  # Assuming 128x128 image
                    y = (tft.height - 128) // 2
                    tft.blit_buffer(no_filter_data, x, y, 128, 128)
                    print("No filter image displayed")
                    del no_filter_data  # Free memory immediately
                    gc.collect()
                except Exception as e:
                    print(f"Error loading no_filter image: {e}")
                    # Fallback: show text
                    tft.fill(gc9a01.BLACK)
                    w = tft.write_width(font, "No Filter!")
                    x = (tft.width - w) // 2
                    y = (tft.height - 32) // 2
                    tft.write(font, "No Filter!", x, y, gc9a01.RED)
                    print("No filter text displayed (fallback)")
                
                # Wait for filter to be inserted
                print("Waiting for filter to be inserted...")
                touch_last_state = touch_pin.value()
                touch_hold_start = None
                while filter_switch.value():  # Keep waiting while no filter (switch is open/high)
                    current_touch = touch_pin.value()
                    now = time.ticks_ms()
                    if touch_last_state == 0 and current_touch == 1:
                        touch_hold_start = now
                    elif touch_last_state == 1 and current_touch == 0:
                        if touch_hold_start is not None:
                            hold_time = time.ticks_diff(now, touch_hold_start)
                            if hold_time >= 2000:
                                print("Touch held for 2 seconds: entering screen off/wake mode")
                                # Turn off screen
                                tft.backlight(False)
                                tft.fill(gc9a01.BLACK)
                                # Wait for tap to wake
                                print("Screen off. Waiting for tap to wake...")
                                # Wait for tap (rising edge)
                                sleep_touch_last = touch_pin.value()
                                while True:
                                    sleep_touch = touch_pin.value()
                                    if sleep_touch_last == 0 and sleep_touch == 1:
                                        break
                                    sleep_touch_last = sleep_touch
                                    time.sleep_ms(20)
                                # Wake up: turn on screen, show ATOMU logo
                                tft.backlight(True)
                                tft.fill(gc9a01.BLACK)
                                try:
                                    gc.collect()
                                    with open("Atomu.raw", "rb") as f:
                                        logo_data = f.read()
                                    x = (tft.width - 200) // 2
                                    y = (tft.height - 200) // 2
                                    tft.blit_buffer(logo_data, x, y, 200, 200)
                                    del logo_data
                                    gc.collect()
                                    print("ATOMU logo displayed (wake)")
                                except Exception as e:
                                    print(f"Error loading ATOMU logo: {e}")
                                    tft.fill(gc9a01.BLACK)
                                    w = tft.write_width(font, "ATOMU")
                                    x = (tft.width - w) // 2
                                    y = (tft.height - 32) // 2
                                    tft.write(font, "ATOMU", x, y, gc9a01.WHITE)
                                    gc.collect()
                                buzzer.value(1)
                                time.sleep_ms(50)
                                buzzer.value(0)
                                # Wait for second tap
                                print("Waiting for second tap to return to no filter check...")
                                sleep_touch_last = touch_pin.value()
                                while True:
                                    sleep_touch = touch_pin.value()
                                    if sleep_touch_last == 0 and sleep_touch == 1:
                                        break
                                    sleep_touch_last = sleep_touch
                                    time.sleep_ms(20)
                                # After second tap, re-enter no filter wait loop
                                print("Second tap detected, returning to no filter check...")
                                tft.fill(gc9a01.BLACK)
                                # Re-display no_filter image and continue loop
                                try:
                                    gc.collect()
                                    with open("no_filter.raw", "rb") as f:
                                        no_filter_data = f.read()
                                    x = (tft.width - 128) // 2
                                    y = (tft.height - 128) // 2
                                    tft.blit_buffer(no_filter_data, x, y, 128, 128)
                                    del no_filter_data
                                    gc.collect()
                                    print("No filter image re-displayed after wake")
                                except Exception as e:
                                    print(f"Error loading no_filter image: {e}")
                                    tft.fill(gc9a01.BLACK)
                                    w = tft.write_width(font, "No Filter!")
                                    x = (tft.width - w) // 2
                                    y = (tft.height - 32) // 2
                                    tft.write(font, "No Filter!", x, y, gc9a01.RED)
                                    gc.collect()
                                # Reset hold state and continue waiting for filter or another hold
                                touch_hold_start = None
                                touch_last_state = touch_pin.value()
                                continue
                            touch_hold_start = None
                    if touch_hold_start is not None:
                        hold_time = time.ticks_diff(now, touch_hold_start)
                        if hold_time >= 2000:
                            print("Touch held for 2 seconds: entering screen off/wake mode")
                            # Turn off screen
                            tft.backlight(False)
                            tft.fill(gc9a01.BLACK)
                            # Wait for tap to wake
                            print("Screen off. Waiting for tap to wake...")
                            sleep_touch_last = touch_pin.value()
                            while True:
                                sleep_touch = touch_pin.value()
                                if sleep_touch_last == 0 and sleep_touch == 1:
                                    break
                                sleep_touch_last = sleep_touch
                                time.sleep_ms(20)
                            # Wake up: turn on screen, show ATOMU logo
                            tft.backlight(True)
                            tft.fill(gc9a01.BLACK)
                            try:
                                gc.collect()
                                with open("Atomu.raw", "rb") as f:
                                    logo_data = f.read()
                                x = (tft.width - 200) // 2
                                y = (tft.height - 200) // 2
                                tft.blit_buffer(logo_data, x, y, 200, 200)
                                del logo_data
                                gc.collect()
                                print("ATOMU logo displayed (wake)")
                            except Exception as e:
                                print(f"Error loading ATOMU logo: {e}")
                                tft.fill(gc9a01.BLACK)
                                w = tft.write_width(font, "ATOMU")
                                x = (tft.width - w) // 2
                                y = (tft.height - 32) // 2
                                tft.write(font, "ATOMU", x, y, gc9a01.WHITE)
                                gc.collect()
                            buzzer.value(1)
                            time.sleep_ms(50)
                            buzzer.value(0)
                            # Wait for second tap
                            print("Waiting for second tap to return to no filter check...")
                            sleep_touch_last = touch_pin.value()
                            while True:
                                sleep_touch = touch_pin.value()
                                if sleep_touch_last == 0 and sleep_touch == 1:
                                    break
                                sleep_touch_last = sleep_touch
                                time.sleep_ms(20)
                            # After second tap, re-enter no filter wait loop
                            print("Second tap detected, returning to no filter check...")
                            tft.fill(gc9a01.BLACK)
                            # Re-display no_filter image and continue loop
                            try:
                                gc.collect()
                                with open("no_filter.raw", "rb") as f:
                                    no_filter_data = f.read()
                                x = (tft.width - 128) // 2
                                y = (tft.height - 128) // 2
                                tft.blit_buffer(no_filter_data, x, y, 128, 128)
                                del no_filter_data
                                gc.collect()
                                print("No filter image re-displayed after wake")
                            except Exception as e:
                                print(f"Error loading no_filter image: {e}")
                                tft.fill(gc9a01.BLACK)
                                w = tft.write_width(font, "No Filter!")
                                x = (tft.width - w) // 2
                                y = (tft.height - 32) // 2
                                tft.write(font, "No Filter!", x, y, gc9a01.RED)
                                gc.collect()
                            # Reset hold state and continue waiting for filter or another hold
                            touch_hold_start = None
                            touch_last_state = touch_pin.value()
                            continue
                    touch_last_state = current_touch
                    time.sleep_ms(20)  # Check every 20ms for more responsive hold detection
                print("Filter inserted - proceeding to main system")
                # Short beep to confirm filter insertion
                buzzer.value(1)
                time.sleep_ms(50)
                buzzer.value(0)
            else:
                print("Filter detected - proceeding to main system")
            
            break  # Exit the wait loop

# Check FRAM for filter value and display appropriate image
print("Reading filter percentage from FRAM...")
try:
    filter_percent = read_filter_percent_fram()
    print(f"Filter percentage read from FRAM: {filter_percent:.2f}%")
except Exception as e:
    print(f"Error reading from FRAM: {e}")
    filter_percent = 0.0
    write_filter_percent_fram(0.0)
    print("Filter percentage initialized to 0.00% in FRAM")

# Display filter status based on percentage
tft.fill(gc9a01.BLACK)

if filter_percent < 85:
    # Normal filter status
    try:
        gc.collect()  # Free memory before loading image
        with open("filter.raw", "rb") as f:
            filter_data = f.read()
        # Position image on top
        x = (tft.width - 128) // 2
        y = 20  # Top area
        tft.blit_buffer(filter_data, x, y, 128, 128)
        print("Filter image displayed")
        del filter_data  # Free memory immediately
        gc.collect()
    except Exception as e:
        print(f"Error loading filter image: {e}")
        # Fallback: show text
        w = tft.write_width(font, "Filter")
        x = (tft.width - w) // 2
        y = 80
        tft.write(font, "Filter", x, y, gc9a01.WHITE)
    
    # Show percentage below image
    percent_text = f"{int(filter_percent)}%"
    w = tft.write_width(font, percent_text)
    x = (tft.width - w) // 2
    y = 160  # Below the image
    tft.write(font, percent_text, x, y, gc9a01.WHITE)
    print(f"Filter percentage displayed: {percent_text}")

elif filter_percent >= 85 and filter_percent < 100:
    # Filter warning status
    try:
        gc.collect()  # Free memory before loading image
        with open("filter_warning.raw", "rb") as f:
            warning_data = f.read()
        # Position image on top
        x = (tft.width - 128) // 2
        y = 20  # Top area
        tft.blit_buffer(warning_data, x, y, 128, 128)
        print("Filter warning image displayed")
        del warning_data  # Free memory immediately
        gc.collect()
    except Exception as e:
        print(f"Error loading filter_warning image: {e}")
        # Fallback: show text
        w = tft.write_width(font, "Filter Warning")
        x = (tft.width - w) // 2
        y = 80
        tft.write(font, "Filter Warning", x, y, gc9a01.YELLOW)
    
    # Show percentage below image
    percent_text = f"{int(filter_percent)}%"
    w = tft.write_width(font, percent_text)
    x = (tft.width - w) // 2
    y = 160  # Below the image
    tft.write(font, percent_text, x, y, gc9a01.YELLOW)
    print(f"Filter warning percentage displayed: {percent_text}")

else:  # filter_percent >= 100
    # Filter reset status - wait for reset button
    print("Filter at 100% - waiting for reset button to be held for 3 seconds")
    
    # Show current status first
    try:
        gc.collect()  # Free memory before loading image
        with open("filter_full.raw", "rb") as f:
            filter_data = f.read()
        # Position image on top
        x = (tft.width - 128) // 2
        y = 20  # Top area
        tft.blit_buffer(filter_data, x, y, 128, 128)
        print("Filter full image displayed")
        del filter_data  # Free memory immediately
        gc.collect()
    except Exception as e:
        print(f"Error loading filter_full image: {e}")
        # Fallback: show text
        w = tft.write_width(font, "Filter Full")
        x = (tft.width - w) // 2
        y = 80
        tft.write(font, "Filter Full", x, y, gc9a01.RED)
    
    # Show percentage below image
    percent_text = f"{int(filter_percent)}%"
    w = tft.write_width(font, percent_text)
    x = (tft.width - w) // 2
    y = 160  # Below the image
    tft.write(font, percent_text, x, y, gc9a01.RED)
    print(f"Filter full percentage displayed: {percent_text}")
    
    # Wait for reset button to be held for 3 seconds
    reset_start_time = None
    reset_held = False
    skipped_reset = False
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
        # Check for tap on touch module to skip reset
        touch_skip_last = touch_pin.value() if 'touch_skip_last' not in locals() else touch_skip_last
        touch_skip_current = touch_pin.value()
        if touch_skip_last == 0 and touch_skip_current == 1:
            print("[INFO] Touch tap detected - skipping filter reset and proceeding to mode selection.")
            skipped_reset = True
            buzzer.value(1)
            time.sleep_ms(50)
            buzzer.value(0)
            break
        touch_skip_last = touch_skip_current
        time.sleep_ms(100)
    if not skipped_reset:
        # Reset filter percentage to 0
        write_filter_percent_fram(0.0)
        filter_percent = 0.0
        print("✓ Filter reset to 0% in FRAM")
        # Show reset confirmation with proper filter_reset image
        tft.fill(gc9a01.BLACK)
        try:
            gc.collect()  # Free memory before loading image
            with open("filter_reset.raw", "rb") as f:
                reset_data = f.read()
            # Position image on top
            x = (tft.width - 128) // 2
            y = 20  # Top area
            tft.blit_buffer(reset_data, x, y, 128, 128)
            print("Filter reset image displayed")
            del reset_data  # Free memory immediately
            gc.collect()
        except Exception as e:
            print(f"Error loading filter_reset image: {e}")
            # Fallback: show text
            w = tft.write_width(font, "Filter Reset!")
            x = (tft.width - w) // 2
            y = 80
            tft.write(font, "Filter Reset!", x, y, gc9a01.GREEN)
        # Show reset percentage
        percent_text = f"{int(filter_percent)}%"
        w = tft.write_width(font, percent_text)
        x = (tft.width - w) // 2
        y = 160  # Below the image
        tft.write(font, percent_text, x, y, gc9a01.GREEN)
        print(f"Filter reset complete: {percent_text}")
        # Two short buzzes to confirm reset (matching low mode behavior)
        buzzer.value(1)
        time.sleep_ms(100)
        buzzer.value(0)
        time.sleep_ms(200)
        buzzer.value(1)
        time.sleep_ms(100)
        buzzer.value(0)

print("Filter status display complete")

# Mode selection section
print("Starting mode selection...")
time.sleep(2)  # Brief pause after filter display

# Mode selection variables
modes = ["low", "medium", "high", "automatic"]
mode_idx = 0
mode_selection_start = None
MODE_SELECTION_TIMEOUT = 3000  # 3 seconds to lock in mode
mode_locked = False

# Show initial mode (low)
current_mode = modes[mode_idx]
print(f"Initial mode: {current_mode}")

# Display the mode image
tft.fill(gc9a01.BLACK)
try:
    gc.collect()  # Free memory before loading image
    with open(f"{current_mode}.raw", "rb") as f:
        mode_data = f.read()
    # Center the 128x128 image
    x = (tft.width - 128) // 2
    y = (tft.height - 128) // 2
    tft.blit_buffer(mode_data, x, y, 128, 128)
    print(f"{current_mode} mode image displayed")
    del mode_data  # Free memory immediately
    gc.collect()
except Exception as e:
    print(f"Error loading {current_mode} image: {e}")
    # Fallback: show text
    w = tft.write_width(font, current_mode.title())
    x = (tft.width - w) // 2
    y = (tft.height - 32) // 2
    tft.write(font, current_mode.title(), x, y, gc9a01.WHITE)

# Mode selection loop
mode_selection_start = time.ticks_ms()
touch_last_state = touch_pin.value()
touch_hold_start = None
TOUCH_HOLD_TIME = 2000  # 2 seconds for hold detection

while not mode_locked:
    current_touch = touch_pin.value()
    now = time.ticks_ms()

    # Edge detection for tap/hold
    if touch_last_state == 0 and current_touch == 1:
        # Touch pressed
        touch_hold_start = now
    elif touch_last_state == 1 and current_touch == 0:
        # Touch released
        if touch_hold_start is not None:
            hold_time = time.ticks_diff(now, touch_hold_start)
            if hold_time < TOUCH_HOLD_TIME:
                # TAP: cycle mode
                print(f"Touch tap detected - changing mode from {current_mode}")
                buzzer.value(1)
                time.sleep_ms(50)
                buzzer.value(0)
                mode_idx = (mode_idx + 1) % len(modes)
                current_mode = modes[mode_idx]
                print(f"Mode changed to: {current_mode}")
                mode_selection_start = now
                tft.fill(gc9a01.BLACK)
                try:
                    gc.collect()
                    with open(f"{current_mode}.raw", "rb") as f:
                        mode_data = f.read()
                    x = (tft.width - 128) // 2
                    y = (tft.height - 128) // 2
                    tft.blit_buffer(mode_data, x, y, 128, 128)
                    print(f"{current_mode} mode image displayed")
                    del mode_data
                    gc.collect()
                except Exception as e:
                    print(f"Error loading {current_mode} image: {e}")
                    w = tft.write_width(font, current_mode.title())
                    x = (tft.width - w) // 2
                    y = (tft.height - 32) // 2
                    tft.write(font, current_mode.title(), x, y, gc9a01.WHITE)
            else:
                # HOLD: (no action for now, could add sleep here if desired)
                print("Touch hold detected (no action)")
            touch_hold_start = None
    # If holding, could add hold action here if needed
    if touch_hold_start is not None:
        hold_time = time.ticks_diff(now, touch_hold_start)
        # (No hold action for now)
    # Timeout to lock in mode
    if time.ticks_diff(now, mode_selection_start) >= MODE_SELECTION_TIMEOUT:
        mode_locked = True
        print(f"Mode locked in: {current_mode}")
        tft.fill(gc9a01.BLACK)
        try:
            with open(f"{current_mode}.raw", "rb") as f:
                mode_data = f.read()
            scaled_data = bytearray()
            for y_pos in range(0, 128, 2):
                for x_pos in range(0, 128, 2):
                    orig_pos = (y_pos * 128 + x_pos) * 2
                    if orig_pos + 1 < len(mode_data):
                        scaled_data.append(mode_data[orig_pos])
                        scaled_data.append(mode_data[orig_pos + 1])
            x = (tft.width - 64) // 2
            y = (tft.height - 64) // 2 - 40
            tft.blit_buffer(scaled_data, x, y, 64, 64)
            print(f"{current_mode} mode locked (64x64 scaled)")
        except Exception as e:
            print(f"Error loading {current_mode} image: {e}")
            w = tft.write_width(font, f"{current_mode.title()} (Locked)")
            x = (tft.width - w) // 2
            y = (tft.height - 32) // 2
            tft.write(font, f"{current_mode.title()} (Locked)", x, y, gc9a01.GREEN)
    touch_last_state = current_touch
    time.sleep_ms(10)

print(f"Mode selection complete - {current_mode} mode is locked in")

# --- PM2.5 Sensor Reading Function ---
def read_sensor():
    """
    Reads PM1.0, PM2.5, and PM10 values from the UART sensor.
    Returns (pm1, pm25, pm10) as integers, or (None, None, None) if not available.
    """
    if uart.any():
        try:
            data = uart.read()
            if data and len(data) >= 32:
                # Typical Plantower protocol: PM1.0 at bytes 4-5, PM2.5 at 6-7, PM10 at 8-9
                pm1 = int.from_bytes(data[4:6], 'big')
                pm25 = int.from_bytes(data[6:8], 'big')
                pm10 = int.from_bytes(data[8:10], 'big')
                return pm1, pm25, pm10
        except Exception as e:
            print(f"Error reading sensor: {e}")
    return None, None, None


# Main operation loop based on selected mode
if current_mode == "low":
    print("Starting LOW mode operation loop...")
    # --- PM2.5 display setup ---
    pm25_last_displayed = None
    pm25_last_update = time.ticks_ms()
    PM25_UPDATE_INTERVAL = 1000  # ms
    
    # Coordinates for PM2.5 value (below the 64x64 image, 15px lower)
    pm25_y = (tft.height - 64) // 2 - 40 + 64 + 16 + 15
    pm25_x_center = tft.width // 2
    pm25_font = pmfont
    pm25_color = gc9a01.WHITE
    pm25_bg_color = gc9a01.BLACK
    
    # PM2.5 color ranges - 3 colors: Persian Green, Orange, Red
    def get_pm25_color(pm25_value):
        """Returns color based on PM2.5 value ranges"""
        if pm25_value <= 35:
            return gc9a01.color565(0, 168, 107)  # Persian Green - Good/Moderate (0-35 µg/m³)
        elif pm25_value <= 150:
            return gc9a01.color565(255, 140, 0)  # Medium Orange - Unhealthy (36-150 µg/m³)
        else:
            return gc9a01.RED  # Red - Very Unhealthy/Hazardous (>150 µg/m³)
    
    # --- Motor setup ---
    def set_motor_brake(on=False):
        brake.value(1 if on else 0)
    def set_motor_speed(percent):
        percent = max(0, min(100, percent))
        duty = int(((100 - percent) / 100) * 65535)
        pwm.duty_u16(duty)
    set_motor_brake(False)
    set_motor_speed(33)
    
    # --- Filter increment setup ---
    filter_last_increment = time.ticks_ms()
    FILTER_INCREMENT_INTERVAL = 1000  # 1 second
    filter_increment_amount = 0.5
    
    # --- Filter reset setup ---
    reset_button_last_state = reset_pin.value()
    reset_button_hold_start = None
    RESET_HOLD_TIME = 3000  # 3 seconds
    
    # --- Filter full detection ---
    filter_full_shown = False
    
    # --- Touch detection setup ---
    TOUCH_HOLD_TIME = 2000  # 3 seconds for hold detection
    touch_last_state = touch_pin.value()
    touch_hold_start = None

    # --- Sleep state management ---
    sleep_mode = False
    wake_stage = 0  # 0: normal, 1: just woke, Atomu image shown

    # --- Mode selection state for tap-to-cycle ---
    mode_selecting = False
    mode_selection_idx = 0  # index in modes
    mode_selection_timer = 0
    mode_selection_locked = False
    modes = ["low", "medium", "high", "automatic"]
    MODE_SELECTION_TIMEOUT = 3000  # ms

    def show_mode_image(mode_name):
        tft.fill(gc9a01.BLACK)
        try:
            gc.collect()
            with open(f"{mode_name}.raw", "rb") as f:
                mode_data = f.read()
            x = (tft.width - 128) // 2
            y = (tft.height - 128) // 2
            tft.blit_buffer(mode_data, x, y, 128, 128)
            del mode_data
            gc.collect()
            print(f"{mode_name} mode image displayed")
        except Exception as e:
            print(f"Error loading {mode_name} image: {e}")
            w = tft.write_width(font, mode_name.title())
            x = (tft.width - w) // 2
            y = (tft.height - 32) // 2
            tft.write(font, mode_name.title(), x, y, gc9a01.WHITE)

    def draw_pm25_value(val):
        clear_w = tft.write_width(pm25_font, "888.8") + 16
        clear_x = pm25_x_center - clear_w // 2
        tft.fill_rect(clear_x, pm25_y, clear_w, 70, pm25_bg_color)
        val_str = f"{int(val):03d}"
        w = tft.write_width(pm25_font, val_str)
        x = pm25_x_center - w // 2
        # Use dynamic color based on PM2.5 value
        dynamic_color = get_pm25_color(val)
        tft.write(pm25_font, val_str, x, pm25_y, dynamic_color)

    while True:
        now = time.ticks_ms()

        # --- Mode selection tap-to-cycle logic ---
        if mode_selecting:
            # Disable PM2.5 updates while selecting mode
            # Show current mode image if just entered selection
            if mode_selection_timer == 0:
                show_mode_image(modes[mode_selection_idx])
                mode_selection_timer = now
            # If timeout, lock in mode
            if time.ticks_diff(now, mode_selection_timer) >= MODE_SELECTION_TIMEOUT:
                mode_selecting = False
                mode_selection_locked = True
                current_mode = modes[mode_selection_idx]
                sleep_mode = False  # Exit sleep mode when mode is locked in
                print(f"Mode locked in: {current_mode}")
                set_motor_brake(False)
                if current_mode != "low":
                    break  # Exit low mode loop to enter new mode
                else:
                    # Show small locked low image and resume low mode
                    tft.fill(gc9a01.BLACK)
                    try:
                        gc.collect()
                        with open("low.raw", "rb") as f:
                            mode_data = f.read()
                        # Simple scaling: take every other pixel to create 64x64 from 128x128
                        scaled_data = bytearray()
                        for y_pos in range(0, 128, 2):  # Skip every other row
                            for x_pos in range(0, 128, 2):  # Skip every other column
                                # Calculate position in original 128x128 image (2 bytes per pixel)
                                orig_pos = (y_pos * 128 + x_pos) * 2
                                if orig_pos + 1 < len(mode_data):
                                    scaled_data.append(mode_data[orig_pos])
                                    scaled_data.append(mode_data[orig_pos + 1])
                        # Position the 64x64 image higher than center
                        x = (tft.width - 64) // 2
                        y = (tft.height - 64) // 2 - 40  # Move 40 pixels higher than center
                        tft.blit_buffer(scaled_data, x, y, 64, 64)
                        print("Low mode image (locked) displayed")
                        del mode_data  # Free memory
                        gc.collect()
                    except Exception as e:
                        print(f"Error loading low image: {e}")
                        # Fallback: show text
                        w = tft.write_width(font, "Low (Locked)")
                        x = (tft.width - w) // 2
                        y = (tft.height - 32) // 2
                        tft.write(font, "Low (Locked)", x, y, gc9a01.GREEN)
                    mode_selection_locked = False  # Reset for next time
                    # Force redraw PM2.5 value immediately
                    pm25_last_displayed = None  # Force update on next cycle
                    # Check if filter is full and redraw filter_full image if needed
                    if filter_full_shown:
                        print("[INFO] Filter is full - redrawing filter_full image")
                        tft.fill(gc9a01.BLACK)
                        try:
                            gc.collect()
                            with open("filter_full.raw", "rb") as f:
                                full_data = f.read()
                            x = (tft.width - 128) // 2
                            y = (tft.height - 128) // 2
                            tft.blit_buffer(full_data, x, y, 128, 128)
                            print("Filter full image redrawn after mode change")
                            del full_data
                            gc.collect()
                        except Exception as e:
                            print(f"Error loading filter_full image: {e}")
                            w = tft.write_width(font, "Filter Full!")
                            x = (tft.width - w) // 2
                            y = (tft.height - 32) // 2
                            tft.write(font, "Filter Full!", x, y, gc9a01.RED)
            # Touch handling for cycling modes is below

        # Only update PM2.5 and filter value if not in mode selection, not filter full, and not showing Atomu logo (wake_stage == 1)
        if not mode_selecting and not filter_full_shown and wake_stage == 0:
            if time.ticks_diff(now, pm25_last_update) >= PM25_UPDATE_INTERVAL:
                pm1, pm25, pm10 = read_sensor()
                if pm25 is not None:
                    if pm25_last_displayed is None or abs(pm25 - pm25_last_displayed) >= 2:
                        draw_pm25_value(pm25)
                        pm25_last_displayed = pm25
                pm25_last_update = now

            # Filter increment every second (disabled in sleep mode)
            if not sleep_mode and time.ticks_diff(now, filter_last_increment) >= FILTER_INCREMENT_INTERVAL:
                filter_percent += filter_increment_amount
                if filter_percent > 100.0:
                    filter_percent = 100.0
                write_filter_percent_fram(filter_percent)
                print(f"Filter incremented to: {filter_percent:.1f}%")
                filter_last_increment = now
                if filter_percent >= 100.0 and not filter_full_shown:
                    print("[INFO] Filter reached 100% - showing filter full warning")
                    filter_full_shown = True
                    tft.fill(gc9a01.BLACK)
                    try:
                        gc.collect()
                        with open("filter_full.raw", "rb") as f:
                            full_data = f.read()
                        x = (tft.width - 128) // 2
                        y = (tft.height - 128) // 2
                        tft.blit_buffer(full_data, x, y, 128, 128)
                        print("Filter full image displayed")
                        del full_data
                        gc.collect()
                    except Exception as e:
                        print(f"Error loading filter_full image: {e}")
                        w = tft.write_width(font, "Filter Full!")
                        x = (tft.width - w) // 2
                        y = (tft.height - 32) // 2
                        tft.write(font, "Filter Full!", x, y, gc9a01.RED)
                    for i in range(3):
                        buzzer.value(1)
                        time.sleep_ms(200)
                        buzzer.value(0)
                        if i < 2:
                            time.sleep_ms(300)

        # Filter reset button logic (unchanged)
        current_reset_state = reset_pin.value()
        if reset_button_last_state == 1 and current_reset_state == 0:
            reset_button_hold_start = now
            print("[DEBUG] Reset button pressed")
        elif reset_button_last_state == 0 and current_reset_state == 1:
            reset_button_hold_start = None
            print("[DEBUG] Reset button released")
        if reset_button_hold_start is not None:
            hold_time = time.ticks_diff(now, reset_button_hold_start)
            if hold_time >= RESET_HOLD_TIME:
                print("[INFO] Reset button held for 3 seconds - resetting filter")
                filter_percent = 0.0
                write_filter_percent_fram(0.0)
                filter_full_shown = False
                tft.fill(gc9a01.BLACK)
                try:
                    gc.collect()
                    with open("filter_reset.raw", "rb") as f:
                        reset_data = f.read()
                    x = (tft.width - 128) // 2
                    y = (tft.height - 128) // 2
                    tft.blit_buffer(reset_data, x, y, 128, 128)
                    print("Filter reset image displayed")
                    del reset_data
                    gc.collect()
                except Exception as e:
                    print(f"Error loading filter_reset image: {e}")
                    w = tft.write_width(font, "Filter Reset!")
                    x = (tft.width - w) // 2
                    y = (tft.height - 32) // 2
                    tft.write(font, "Filter Reset!", x, y, gc9a01.GREEN)
                buzzer.value(1)
                time.sleep_ms(100)
                buzzer.value(0)
                time.sleep_ms(200)
                buzzer.value(1)
                time.sleep_ms(100)
                buzzer.value(0)
                time.sleep(3)
                tft.fill(gc9a01.BLACK)
                try:
                    gc.collect()
                    with open("low.raw", "rb") as f:
                        mode_data = f.read()
                    scaled_data = bytearray()
                    for y_pos in range(0, 128, 2):
                        for x_pos in range(0, 128, 2):
                            orig_pos = (y_pos * 128 + x_pos) * 2
                            if orig_pos + 1 < len(mode_data):
                                scaled_data.append(mode_data[orig_pos])
                                scaled_data.append(mode_data[orig_pos + 1])
                    x = (tft.width - 64) // 2
                    y = (tft.height - 64) // 2 - 40
                    tft.blit_buffer(scaled_data, x, y, 64, 64)
                    print("Low mode image restored")
                except Exception as e:
                    print(f"Error restoring low mode image: {e}")
                    w = tft.write_width(font, "Low (Locked)")
                    x = (tft.width - w) // 2
                    y = (tft.height - 32) // 2
                    tft.write(font, "Low (Locked)", x, y, gc9a01.GREEN)
                reset_button_hold_start = None
                reset_button_last_state = current_reset_state
                print("Filter reset complete - returning to low mode")
                pm25_last_displayed = None
        reset_button_last_state = current_reset_state

        # --- Touch event handling for tap/hold and sleep/wake stages ---
        current_touch = touch_pin.value()
        if sleep_mode:
            # Device is in sleep, only respond to tap
            if touch_last_state == 0 and current_touch == 1:
                # First tap after sleep: show Atomu image and filter percentage
                tft.backlight(True)
                tft.fill(gc9a01.BLACK)
                try:
                    gc.collect()
                    with open("Atomu.raw", "rb") as f:
                        logo_data = f.read()
                    x = (tft.width - 200) // 2
                    y = (tft.height - 200) // 2
                    tft.blit_buffer(logo_data, x, y, 200, 200)
                    del logo_data
                    gc.collect()
                    print("ATOMU logo displayed (wake)")
                except Exception as e:
                    print(f"Error loading ATOMU logo: {e}")
                    tft.fill(gc9a01.BLACK)
                    w = tft.write_width(font, "ATOMU")
                    x = (tft.width - w) // 2
                    y = (tft.height - 32) // 2
                    tft.write(font, "ATOMU", x, y, gc9a01.WHITE)
                    gc.collect()
                buzzer.value(1)
                time.sleep_ms(50)
                buzzer.value(0)
                sleep_mode = False
                wake_stage = 1  # Now waiting for second tap
            touch_last_state = current_touch
            time.sleep_ms(20)
            continue  # Skip rest of loop while in sleep/wake
        elif wake_stage == 1:
            # Waiting for second tap to check filter
            if touch_last_state == 0 and current_touch == 1:
                # Second tap: check filter before mode selection
                buzzer.value(1)
                time.sleep_ms(50)
                buzzer.value(0)
                # Check filter microswitch
                if filter_switch.value():  # No filter installed (switch is open/high)
                    print("No filter detected after wake")
                    tft.fill(gc9a01.BLACK)
                    # Show no_filter image
                    try:
                        gc.collect()
                        with open("no_filter.raw", "rb") as f:
                            no_filter_data = f.read()
                        x = (tft.width - 128) // 2
                        y = (tft.height - 128) // 2
                        tft.blit_buffer(no_filter_data, x, y, 128, 128)
                        del no_filter_data
                        gc.collect()
                        print("No filter image displayed (wake)")
                    except Exception as e:
                        print(f"Error loading no_filter image: {e}")
                        tft.fill(gc9a01.BLACK)
                        w = tft.write_width(font, "No Filter!")
                        x = (tft.width - w) // 2
                        y = (tft.height - 32) // 2
                        tft.write(font, "No Filter!", x, y, gc9a01.RED)
                    # Wait for filter to be inserted, but also listen for touch hold
                    print("Waiting for filter to be inserted (wake)... Listening for touch hold...")
                    touch_last_state_nf = touch_pin.value()
                    touch_hold_start_nf = None
                    lcd_off_triggered = False
                    while filter_switch.value():
                        current_touch_nf = touch_pin.value()
                        now_nf = time.ticks_ms()
                        if touch_last_state_nf == 0 and current_touch_nf == 1:
                            touch_hold_start_nf = now_nf
                        # If holding, check hold time and turn off LCD immediately at 2s
                        if touch_hold_start_nf is not None and current_touch_nf == 1:
                            hold_time_nf = time.ticks_diff(now_nf, touch_hold_start_nf)
                            if hold_time_nf >= 2000 and not lcd_off_triggered:
                                print("Touch held for 2 seconds while waiting for filter after wake: turning off LCD immediately.")
                                tft.backlight(False)
                                tft.fill(gc9a01.BLACK)
                                lcd_off_triggered = True
                                # After turning off, listen for a tap to wake
                                print("LCD off. Waiting for tap to wake and show ATOMU logo...")
                                sleep_touch_last = touch_pin.value()
                                while True:
                                    sleep_touch = touch_pin.value()
                                    if sleep_touch_last == 0 and sleep_touch == 1:
                                        # Tap detected, wake up
                                        tft.backlight(True)
                                        tft.fill(gc9a01.BLACK)
                                        try:
                                            gc.collect()
                                            with open("Atomu.raw", "rb") as f:
                                                logo_data = f.read()
                                            x = (tft.width - 200) // 2
                                            y = (tft.height - 200) // 2
                                            tft.blit_buffer(logo_data, x, y, 200, 200)
                                            del logo_data
                                            gc.collect()
                                            print("ATOMU logo displayed (wake after LCD off)")
                                        except Exception as e:
                                            print(f"Error loading ATOMU logo: {e}")
                                            tft.fill(gc9a01.BLACK)
                                            w = tft.write_width(font, "ATOMU")
                                            x = (tft.width - w) // 2
                                            y = (tft.height - 32) // 2
                                            tft.write(font, "ATOMU", x, y, gc9a01.WHITE)
                                            gc.collect()
                                        buzzer.value(1)
                                        time.sleep_ms(50)
                                        buzzer.value(0)
                                        break
                                    sleep_touch_last = sleep_touch
                                    time.sleep_ms(20)
                                # After waking, break out of the filter wait loop to resume normal operation
                                break
                        elif touch_last_state_nf == 1 and current_touch_nf == 0:
                            touch_hold_start_nf = None
                            lcd_off_triggered = False
                        touch_last_state_nf = current_touch_nf
                        time.sleep_ms(20)
                    print("Filter inserted after wake - proceeding to filter status display")
                    buzzer.value(1)
                    time.sleep_ms(50)
                    buzzer.value(0)
                # Now show filter percentage and image for 3 seconds
                tft.fill(gc9a01.BLACK)
                gc.collect()
                filter_img = None
                filter_color = gc9a01.WHITE
                percent_text = f"{int(filter_percent)}%"
                if filter_percent < 85:
                    img_file = "filter.raw"
                    filter_color = gc9a01.WHITE
                elif filter_percent < 100:
                    img_file = "filter_warning.raw"
                    filter_color = gc9a01.YELLOW
                else:
                    img_file = "filter_full.raw"
                    filter_color = gc9a01.RED
                try:
                    with open(img_file, "rb") as f:
                        filter_img = f.read()
                    x = (tft.width - 128) // 2
                    y = 20
                    tft.blit_buffer(filter_img, x, y, 128, 128)
                    del filter_img
                    gc.collect()
                    print(f"{img_file} displayed (wake)")
                except Exception as e:
                    print(f"Error loading {img_file}: {e}")
                    w = tft.write_width(font, "Filter")
                    x = (tft.width - w) // 2
                    y = 80
                    tft.write(font, "Filter", x, y, filter_color)
                    gc.collect()
                # Show percentage below image
                w = tft.write_width(font, percent_text)
                x = (tft.width - w) // 2
                y = 160
                tft.write(font, percent_text, x, y, filter_color)
                print(f"Filter percentage displayed: {percent_text}")
                # Wait 3 seconds
                time.sleep(3)
                # Now proceed to mode selection
                tft.fill(gc9a01.BLACK)
                mode_selecting = True
                mode_selection_idx = 0  # Always start from low
                mode_selection_timer = 0
                wake_stage = 0
                print("[DEBUG] Second tap after wake - filter checked, filter status shown, entering mode selection")
            touch_last_state = current_touch
            time.sleep_ms(20)
            continue  # Skip rest of loop while in wake_stage
        # --- Normal operation below ---
        if touch_last_state == 0 and current_touch == 1:
            touch_hold_start = now
            print("[DEBUG] Touch detected - starting hold timer")
        elif touch_last_state == 1 and current_touch == 0:
            if touch_hold_start is not None:
                hold_time = time.ticks_diff(now, touch_hold_start)
                if hold_time < TOUCH_HOLD_TIME:
                    # TAP: Start or continue mode selection
                    print("[DEBUG] User tapped")
                    # Short buzz for tap feedback
                    buzzer.value(1)
                    time.sleep_ms(50)  # 0.05 seconds
                    buzzer.value(0)
                    if not mode_selecting:
                        tft.backlight(True)  # Turn on backlight when starting mode selection
                        mode_selecting = True
                        mode_selection_idx = 0  # Always start from low
                        mode_selection_timer = 0
                        print("[DEBUG] Entering mode selection")
                    else:
                        # Cycle to next mode
                        mode_selection_idx = (mode_selection_idx + 1) % len(modes)
                        show_mode_image(modes[mode_selection_idx])
                        mode_selection_timer = now  # Reset timer
                        print(f"[DEBUG] Cycled to mode: {modes[mode_selection_idx]}")
                else:
                    # HOLD: (3 seconds or more)
                    print("[DEBUG] User held for 3+ seconds")
                    # (No hold action for now)
                touch_hold_start = None
        if touch_hold_start is not None:
            hold_time = time.ticks_diff(now, touch_hold_start)
            if hold_time >= TOUCH_HOLD_TIME:
                set_motor_brake(True)
                tft.fill(gc9a01.BLACK)  # Clear display before sleep
                tft.backlight(False)
                sleep_mode = True  # Set sleep mode flag
                print("[INFO] Entered sleep mode: motor braked, LCD off, filter increment disabled. Waiting for tap to wake.")
                # Wait for tap to wake up
                # (No hold action for now)
                touch_hold_start = None
        touch_last_state = current_touch
        time.sleep_ms(20)

elif current_mode == "medium":
    print("Starting MEDIUM mode operation loop...")
    while True:
        # TODO: Implement medium mode logic
        time.sleep_ms(20)

elif current_mode == "high":
    print("Starting HIGH mode operation loop...")
    while True:
        # TODO: Implement high mode logic
        time.sleep_ms(20)

elif current_mode == "automatic":
    print("Starting AUTOMATIC mode operation loop...")
    while True:
        # TODO: Implement automatic mode logic
        time.sleep_ms(20)

