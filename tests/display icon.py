from machine import SPI, Pin
import gc9a01py as gc9a01
import time

# Setup
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

# Image info
width = 200
height = 200
x = (tft.width - width) // 2
y = (tft.height - height) // 2

# Read raw RGB565 data
with open("Atomu-1.raw", "rb") as f:
    buf = f.read()

print(f"Buffer size: {len(buf)} bytes")  # Should be width * height * 2
tft.blit_buffer(buf, x, y, width, height)
time.sleep(5)
