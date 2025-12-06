#!/usr/bin/env python3
"""
Test script to verify filter increment functionality
This script tests that the filter percentage increases when the motor is running
"""

from machine import Pin, PWM
import utime as time
import os

# Pin assignments (same as main.py)
PWM_PIN = 4
BR_PIN = 5
FR_PIN = 6
FG_PIN = 7

# Motor control functions
def set_speed(percent):
    global current_motor_speed
    percent = max(0, min(100, percent))
    duty = int(((100 - percent) / 100) * 65535)
    pwm.duty_u16(duty)
    current_motor_speed = percent
    print(f"[DEBUG] Motor speed set to: {current_motor_speed}%")

def set_direction(forward=True):
    direction.value(1 if forward else 0)

def set_brake(on=False):
    brake.value(1 if on else 0)

# Initialize motor
pwm = PWM(Pin(PWM_PIN))
pwm.freq(25000)
brake = Pin(BR_PIN, Pin.OUT)
direction = Pin(FR_PIN, Pin.OUT)
fg = Pin(FG_PIN, Pin.IN)

# Initialize motor state
current_motor_speed = 0
set_brake(False)
set_direction(True)

# Filter tracking variables
filter_percent = 0.0
last_filter_increment = 0
FILTER_INCREMENT_INTERVAL = 1000  # 1 second

def read_filter_percent():
    global filter_percent
    try:
        os.mkdir("data")
    except OSError:
        pass
    filter_path = "data/filter.txt"
    if not "filter.txt" in os.listdir("data"):
        with open(filter_path, "w") as f:
            f.write("0.0")
        filter_percent = 0.0
    else:
        with open(filter_path, "r") as f:
            try:
                filter_percent = float(f.read())
            except:
                filter_percent = 0.0
    return filter_percent

def write_filter_percent(val):
    with open("data/filter.txt", "w") as f:
        f.write(f"{val:.2f}")

def test_filter_increment():
    """Test filter increment over time"""
    global filter_percent, last_filter_increment
    
    print("=== Filter Increment Test ===")
    print("This test will run the motor at different speeds and monitor filter increment")
    print("Starting filter percentage:", read_filter_percent())
    
    # Test speeds
    test_speeds = [30, 50, 60, 75]  # low, medium, high, max
    test_duration = 5  # seconds per speed
    
    for speed in test_speeds:
        print(f"\n--- Testing speed: {speed}% ---")
        set_speed(speed)
        
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < test_duration * 1000:
            now = time.ticks_ms()
            
            # Increment filter usage based on motor speed every 1 second
            if time.ticks_diff(now, last_filter_increment) > FILTER_INCREMENT_INTERVAL:
                if current_motor_speed > 0:
                    increment = current_motor_speed / 30.0
                    filter_percent += increment
                    if filter_percent > 100.0:
                        filter_percent = 100.0
                    write_filter_percent(filter_percent)
                    print(f"[{time.ticks_diff(now, start_time)/1000:.1f}s] Filter increment: +{increment:.2f}% (motor: {current_motor_speed}%), Total: {filter_percent:.2f}%")
                else:
                    print(f"[{time.ticks_diff(now, start_time)/1000:.1f}s] Motor not running, skipping increment")
                last_filter_increment = now
            
            time.sleep(0.1)
    
    # Stop motor
    set_speed(0)
    set_brake(True)
    
    print(f"\n=== Test Complete ===")
    print(f"Final filter percentage: {filter_percent:.2f}%")
    print("Expected increment per second:")
    for speed in test_speeds:
        expected = speed / 30.0
        print(f"  Speed {speed}%: +{expected:.2f}% per second")

if __name__ == "__main__":
    try:
        test_filter_increment()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    finally:
        print("Stopping motor and cleaning up...")
        set_speed(0)
        set_brake(True) 