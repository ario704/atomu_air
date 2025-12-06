from machine import Pin
import time

buzzer = Pin(18, Pin.OUT)

buzzer.value(1)  # Beep on
time.sleep(0.05)
buzzer.value(0)  # Beep off

