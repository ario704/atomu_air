from machine import UART, Pin
import time

# Initialize UART
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

# Initialize 'set' pin (GP9) as output
set_pin = Pin(9, Pin.OUT)

print("Cycling sensor power via set pin (GP9)...")

def read_frame():
    if uart.any():
        data = uart.read(32)
        if data and len(data) >= 16 and data[0] == 0x42 and data[1] == 0x4d:
            pm1 = data[10] << 8 | data[11]
            pm25 = data[12] << 8 | data[13]
            pm10 = data[14] << 8 | data[15]
            print(f"PM1.0: {pm1} , PM2.5: {pm25} , PM10: {pm10} ")
        else:
            print("Invalid, partial, or no frame")
    else:
        print("No data yet")

while True:
    # Turn device OFF (fan stops)
    set_pin.value(0)
    print("Device OFF (set pin LOW) for 10 seconds...")
    time.sleep(10)

    # Turn device ON (fan spins)
    set_pin.value(1)
    print("Device ON (set pin HIGH) for 10 seconds, collecting data...")
    start_time = time.time()
    while time.time() - start_time < 10:
        read_frame()
        time.sleep(1)
