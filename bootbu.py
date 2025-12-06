from machine import Pin, SPI
import gc9a01py as gc9a01
import utime as time
import struct
from fonts import NotoSans_32 as font
from fram import init_fram, read_filter_percent_fram, write_filter_percent_fram

# Initialize FRAM
print("Initializing FRAM...")
try:
    fram_success = init_fram()
    if fram_success:
        print("✓ FRAM initialized successfully")
    else:
        print("✗ FRAM initialization failed")
        print("Error: FRAM is required for operation")
        # Just halt with error message - display will be set up later
        while True:
            time.sleep(1)
except Exception as e:
    print(f"✗ FRAM initialization error: {e}")
    print("Error: FRAM is required for operation")
    # Just halt with error message - display will be set up later
    while True:
        time.sleep(1)

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

# Constants
FILTER_SWITCH = Pin(8, Pin.IN, Pin.PULL_UP)
ICON_W = 128
ICON_H = 128
ICON_Y = (tft.height - ICON_H) // 2  # Center the image properly
TEXT_Y = ICON_Y + ICON_H + 16

# Helper: Draw centered raw image (for no_filter only)
def show_centered_icon(filename):
    try:
        with open(filename, "rb") as f:
            buf = f.read()
        x = (tft.width - ICON_W) // 2
        tft.blit_buffer(buf, x, ICON_Y, ICON_W, ICON_H)
    except Exception as e:
        print("Error loading icon:", filename, e)

# Helper: Draw raw image at original position (for filter and filter_warning)
def show_icon(filename):
    try:
        with open(filename, "rb") as f:
            buf = f.read()
        # Position the image higher to give more space for text
        x = (tft.width - ICON_W) // 2
        y = ICON_Y - 20  # Move image up by 20 pixels
        tft.blit_buffer(buf, x, y, ICON_W, ICON_H)
    except Exception as e:
        print("Error loading icon:", filename, e)

# Helper: Show centered text
def show_centered_text(text, y, color=gc9a01.WHITE):
    w = tft.write_width(font, text)
    x = (tft.width - w) // 2
    tft.write(font, text, x, y, color)

# Helper: Show centered text for higher positioned images
def show_centered_text_high(text, y, color=gc9a01.WHITE):
    w = tft.write_width(font, text)
    x = (tft.width - w) // 2
    # Adjust y position to match the higher image position
    adjusted_y = y - 20
    tft.write(font, text, x, adjusted_y, color)

# Splash screen
tft.fill(gc9a01.BLACK)
show_centered_text("ATOMU", 100)
print("Atomu")
time.sleep(3)

# Wait for filter to be installed (draw only once)
if FILTER_SWITCH.value():
    tft.fill(gc9a01.BLACK)
    show_centered_icon("no_filter.raw")
    print("No Filter!")

    # Wait loop (no redraw)
    while FILTER_SWITCH.value():
        time.sleep(0.1)

# Read filter % from FRAM
print("Reading filter percentage from FRAM...")
try:
    filter_percent = read_filter_percent_fram()
    print(f"✓ Filter percent read from FRAM: {filter_percent:.2f}%")
except Exception as e:
    print(f"✗ Error reading from FRAM: {e}")
    # Initialize filter to 0 if read fails
    filter_percent = 0.0
    write_filter_percent_fram(0.0)
    print("✓ Filter initialized to 0.00% in FRAM")

# Display correct filter status
tft.fill(gc9a01.BLACK)

if filter_percent >= 100.0:
    # Filter is full - wait for reset
    show_icon("filter_warning.raw")
    show_centered_text_high("Filter Full!", TEXT_Y)
    show_centered_text_high("Hold Reset 3s", TEXT_Y + 40)
    print(f"Filter: {filter_percent:.2f}% - WAITING FOR RESET")
    
    # Wait for reset button to be held for 3 seconds
    reset_start_time = None
    reset_held = False
    
    while not reset_held:
        # Check if reset button is pressed
        if Pin(3, Pin.IN, Pin.PULL_UP).value() == 0:  # Button pressed (active low)
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
    write_filter_percent_fram(0.0)
    print("✓ Filter reset to 0.00% in FRAM")
    filter_percent = 0.0
    
    # Show reset confirmation
    tft.fill(gc9a01.BLACK)
    show_icon("filter.raw")
    show_centered_text_high("Filter Reset!", TEXT_Y)
    show_centered_text_high("0.00%", TEXT_Y + 40)
    time.sleep(2)
    print("[INFO] Filter reset complete")
    
elif filter_percent >= 85:
    show_icon("filter_warning.raw")
    show_centered_text_high(f"Filter: {int(filter_percent)}%", TEXT_Y)
    print(f"Filter: {int(filter_percent)}%")
    time.sleep(3)
else:
    show_icon("filter.raw")
    show_centered_text_high(f"Filter: {int(filter_percent)}%", TEXT_Y)
    print(f"Filter: {int(filter_percent)}%")
time.sleep(3)

# Start the main program
print("[INFO] Starting main program...")
import main 