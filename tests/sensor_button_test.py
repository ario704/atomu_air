from machine import Pin, UART
import utime as time

# Test sensor reading
print("=== Sensor Test ===")
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

def read_sensor():
    pm1 = pm25 = pm10 = None
    tries = 0
    while tries < 5:
        available = uart.any()
        print(f"UART available: {available}")
        if available >= 32:
            data = uart.read(32)
            print(f"UART data: {data}")
            if data and len(data) == 32 and data[0] == 0x42 and data[1] == 0x4d:
                pm1 = data[10] << 8 | data[11]
                pm25 = data[12] << 8 | data[13]
                pm10 = data[14] << 8 | data[15]
                print(f"PM1: {pm1}, PM2.5: {pm25}, PM10: {pm10}")
                break
        tries += 1
        time.sleep(0.1)
    return pm1, pm25, pm10

# Test sensor for 10 seconds
print("Testing sensor for 10 seconds...")
start_time = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), start_time) < 10000:
    pm1, pm25, pm10 = read_sensor()
    if pm25 is not None:
        print(f"✓ Sensor working: PM2.5 = {pm25}")
    else:
        print("✗ No sensor data")
    time.sleep(1)

# Test reset button
print("\n=== Reset Button Test ===")
reset_pin = Pin(3, Pin.IN, Pin.PULL_UP)
print("Press and hold reset button (GP3) for 3 seconds...")

reset_start_time = None
reset_held = False

while not reset_held:
    if reset_pin.value() == 0:  # Button pressed (active low)
        if reset_start_time is None:
            reset_start_time = time.ticks_ms()
            print("Reset button pressed, starting timer")
    else:
        if reset_start_time is not None:
            print("Reset button released, resetting timer")
            reset_start_time = None
    
    if reset_start_time is not None:
        hold_time = time.ticks_diff(time.ticks_ms(), reset_start_time)
        print(f"Hold time: {hold_time}ms")
        if hold_time >= 3000:  # 3 seconds
            reset_held = True
            print("✓ Reset button held for 3 seconds!")
    
    time.sleep(0.1)

print("Test complete!") 