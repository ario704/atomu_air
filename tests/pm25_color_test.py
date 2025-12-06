from machine import Pin, SPI
import gc9a01py as gc9a01
import utime as time
from fonts import NotoSans_64 as pmfont

# Initialize display
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

# PM2.5 color ranges - 3 colors: Persian Green, Orange, Red
def get_pm25_color(pm25_value):
    """Returns color based on PM2.5 value ranges"""
    if pm25_value <= 35:
        return gc9a01.color565(0, 168, 107)  # Persian Green - Good/Moderate (0-35 µg/m³)
    elif pm25_value <= 150:
        return gc9a01.color565(255, 140, 0)  # Medium Orange - Unhealthy (36-150 µg/m³)
    else:
        return gc9a01.RED  # Red - Very Unhealthy/Hazardous (>150 µg/m³)

def draw_pm25_value(val, color):
    """Draw PM2.5 value with specified color"""
    tft.fill(gc9a01.BLACK)
    
    # Draw the value
    val_str = f"{int(val):03d}"
    w = tft.write_width(pmfont, val_str)
    x = (tft.width - w) // 2
    y = (tft.height - 64) // 2
    tft.write(pmfont, val_str, x, y, color)
    
    # Draw the range description
    if val <= 35:
        desc = "Good/Moderate"
    elif val <= 150:
        desc = "Unhealthy"
    else:
        desc = "Very Unhealthy"
    
    # Draw description below the value (using simple text)
    # Note: Using basic text drawing since font14 might not be available
    print(f"Displaying: {value} µg/m³ - {desc}")

# Test values for each color range
test_values = [
    (15, "Good/Moderate - Persian Green"),
    (80, "Unhealthy - Orange"),
    (200, "Very Unhealthy - Red")
]

print("Starting PM2.5 color test...")
print("Each color will display for 3 seconds")

for value, description in test_values:
    print(f"Showing {value} µg/m³ - {description}")
    color = get_pm25_color(value)
    draw_pm25_value(value, color)
    time.sleep(3)

print("Color test complete!")
tft.fill(gc9a01.BLACK)
# Draw completion message using the large font
tft.write(pmfont, "DONE", 80, 120, gc9a01.WHITE) 