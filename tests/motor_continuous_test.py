#!/usr/bin/env python3
"""
Test script to verify motor behavior during mode selection.
This tests that the motor keeps running at the same speed during mode selection
and only changes when a new mode gets locked in.
"""

from machine import Pin, PWM
import utime as time

# Motor control setup
PWM_PIN = 4
BR_PIN = 5
FR_PIN = 6
FG_PIN = 7

def set_speed(percent):
    percent = max(0, min(100, percent))
    duty = int(((100 - percent) / 100) * 65535)
    pwm.duty_u16(duty)
    print(f"[MOTOR] Speed set to: {percent}%")

pwm = PWM(Pin(PWM_PIN))
pwm.freq(25000)
brake = Pin(BR_PIN, Pin.OUT)
direction = Pin(FR_PIN, Pin.OUT)

# Mode speeds
MODE_SPEEDS = {
    "low": 30,
    "medium": 50,
    "high": 60,
    "max": 75
}

MODES = ["low", "medium", "high", "automatic"]

# Test state
mode_idx = 0
mode_locked = False
target_motor_speed = MODE_SPEEDS[MODES[mode_idx]]
mode_selection_start = time.ticks_ms()
MODE_SELECTION_TIMEOUT = 3000  # 3 seconds

print(f"[TEST] Starting motor continuous test")
print(f"[TEST] Initial mode: {MODES[mode_idx]}, target speed: {target_motor_speed}%")

try:
    while True:
        now = time.ticks_ms()
        
        # Simulate mode cycling every 2 seconds for testing
        if time.ticks_diff(now, mode_selection_start) > 2000:
            if not mode_locked:
                # Cycle to next mode
                mode_idx = (mode_idx + 1) % len(MODES)
                mode_selection_start = now
                print(f"[TEST] Cycling to mode: {MODES[mode_idx]}")
            else:
                # Unlock mode
                mode_locked = False
                mode_selection_start = now
                print(f"[TEST] Unlocking mode selection")
        
        # Check if mode selection timeout has expired
        if mode_selection_start is not None and not mode_locked:
            if time.ticks_diff(now, mode_selection_start) >= MODE_SELECTION_TIMEOUT:
                # Timeout - lock in the current mode
                mode_locked = True
                mode_selection_start = None
                print(f"[TEST] Mode locked in: {MODES[mode_idx]}")
        
        # Motor control logic
        if mode_locked:
            # Mode is locked - calculate new target speed
            mode = MODES[mode_idx]
            if mode == "automatic":
                # Simulate automatic mode with fixed speed for testing
                target_motor_speed = MODE_SPEEDS["medium"]
                print(f"[TEST] Automatic mode - target speed: {target_motor_speed}%")
            else:
                target_motor_speed = MODE_SPEEDS[mode]
                print(f"[TEST] Manual mode {mode} - target speed: {target_motor_speed}%")
            
            # Apply the target speed to motor
            set_speed(target_motor_speed)
        else:
            # Mode not locked - keep running at current target speed
            set_speed(target_motor_speed)
            print(f"[TEST] Mode selection - motor running at: {target_motor_speed}%")
        
        print(f"[TEST] State - Mode: {MODES[mode_idx]}, Locked: {mode_locked}, Target Speed: {target_motor_speed}%")
        print("---")
        
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\n[TEST] Stopping motor")
    set_speed(0)
    brake.value(1) 