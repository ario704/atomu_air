from machine import Pin, PWM
import time

# ===== GPIO Pin Setup =====
PWM_PIN = 4   # EXC - speed control (PWM output)
BR_PIN  = 5   # BR - brake (HIGH = brake engaged)
FR_PIN  = 6   # FR - forward/reverse
FG_PIN  = 7   # FG - tachometer output (input)

# ===== Fan Control Pins =====
pwm = PWM(Pin(PWM_PIN))
pwm.freq(25000)  # 25kHz is standard for fan control

brake = Pin(BR_PIN, Pin.OUT)
direction = Pin(FR_PIN, Pin.OUT)
fg = Pin(FG_PIN, Pin.IN)

# ===== Pulse Counting =====
pulse_count = 0

def count_fg(pin):
    global pulse_count
    pulse_count += 1

fg.irq(trigger=Pin.IRQ_RISING, handler=count_fg)

# ===== Helper Functions =====
def set_speed(percent):
    """Set fan speed as a percentage (0–100%), inverted PWM"""
    percent = max(0, min(100, percent))
    duty = int(((100 - percent) / 100) * 65535)
    pwm.duty_u16(duty)

def set_direction(forward=True):
    direction.value(1 if forward else 0)

def set_brake(on=False):
    """Engage brake if on=True (HIGH = brake engaged)"""
    brake.value(1 if on else 0)

def read_rpm(pulses_per_rev=2):
    global pulse_count
    pulse_count = 0
    time.sleep(1)
    pulses = pulse_count
    rpm = (pulses / pulses_per_rev) * 60
    return int(rpm)

# ===== Startup Sequence =====
print("Initializing motor...")
set_brake(False)      # Brake released
set_direction(True)   # Set forward direction
set_speed(50)         # Start at 50% speed
time.sleep(2)

# ===== Main Loop =====
try:
    while True:
        rpm = read_rpm()
        print("Fan RPM:", rpm)

        for spd in range(40, 91, 10):
            print(f"Setting speed: {spd}%")
            set_speed(spd)
            time.sleep(2)

        print("Reversing direction...")
        set_direction(False)
        time.sleep(5)

        print("Applying brake...")
        set_brake(True)
        time.sleep(3)

        print("Releasing brake and resuming...")
        set_brake(False)
        set_direction(True)
        set_speed(60)
        time.sleep(3)

except KeyboardInterrupt:
    print("Stopping motor...")
    set_speed(0)
    set_brake(True)
