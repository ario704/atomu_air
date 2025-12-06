from machine import Pin, SPI
import gc9a01py as gc9a01
import utime as time
from fonts import NotoSans_32 as font
import gc

# Force garbage collection at start
gc.collect()
print(f"Free memory: {gc.mem_free()} bytes")

# Initialize Display
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

# Define icons to cycle through
ICONS = [
    "low.raw",
    "medium.raw", 
    "high.raw",
    "filter.raw",
    "filter_warning.raw",
    "no_filter.raw",
    "Atomu.raw",
    "automatic.raw",
    "filter_full.raw",
    "filter_reset.raw"
]

# Icon display settings
ICON_W = 128
ICON_H = 128
ICON_Y = (tft.height - ICON_H) // 2  # Center vertically
TEXT_Y = ICON_Y + ICON_H + 16

def show_icon(filename):
    """Display an icon from raw file with memory management"""
    try:
        # Force garbage collection before loading new image
        gc.collect()
        print(f"Loading {filename}...")
        
        with open(filename, "rb") as f:
            buf = f.read()
        
        print(f"Image loaded: {len(buf)} bytes")
        
        x = (tft.width - ICON_W) // 2
        tft.blit_buffer(buf, x, ICON_Y, ICON_W, ICON_H)
        
        # Clear the buffer from memory immediately
        del buf
        gc.collect()
        
        print(f"✓ {filename} displayed")
        return True
    except MemoryError as e:
        print(f"✗ Memory error loading {filename}: {e}")
        return False
    except Exception as e:
        print(f"✗ Error loading {filename}: {e}")
        return False

def show_centered_text(text, y, color=gc9a01.WHITE):
    """Display centered text"""
    w = tft.write_width(font, text)
    x = (tft.width - w) // 2
    tft.write(font, text, x, y, color)

def show_icon_with_fallback(filename):
    """Show icon with fallback text if image fails to load"""
    tft.fill(gc9a01.BLACK)
    
    # Try to show the icon
    if show_icon(filename):
        # Show filename below icon
        show_centered_text(filename.replace('.raw', ''), TEXT_Y, gc9a01.WHITE)
    else:
        # Fallback: show text only
        icon_name = filename.replace('.raw', '').replace('_', ' ').title()
        show_centered_text(icon_name, ICON_Y + 50, gc9a01.RED)
        show_centered_text("(Image Missing)", TEXT_Y, gc9a01.YELLOW)

# Main test loop
print("=== Icon Cycle Test ===")
print(f"Cycling through {len(ICONS)} icons, 3 seconds each...")

for i, icon in enumerate(ICONS, 1):
    print(f"\n[{i}/{len(ICONS)}] Showing {icon}...")
    print(f"Free memory before: {gc.mem_free()} bytes")
    
    show_icon_with_fallback(icon)
    
    print(f"Free memory after: {gc.mem_free()} bytes")
    time.sleep(3)

print("\n=== Test Complete ===")
print("All icons have been displayed!")

# Final message
tft.fill(gc9a01.BLACK)
show_centered_text("Icon Test Complete!", ICON_Y + 50, gc9a01.GREEN)
show_centered_text("All icons shown", TEXT_Y, gc9a01.WHITE) 