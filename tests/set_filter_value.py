from machine import I2C, Pin
import time
from fram import init_fram, write_filter_percent_fram, read_filter_percent_fram

# Initialize FRAM
print("Initializing FRAM...")
try:
    fram_success = init_fram()
    if fram_success:
        print("✓ FRAM initialized successfully")
    else:
        print("✗ FRAM initialization failed")
        raise Exception("FRAM is required for operation")
except Exception as e:
    print(f"✗ FRAM initialization error: {e}")
    raise

# Set the filter percentage value here
FILTER_PERCENTAGE = 100  # Change this value to what you want

print(f"Setting filter percentage to: {FILTER_PERCENTAGE}%")

# Read current value first
try:
    current_value = read_filter_percent_fram()
    print(f"Current filter percentage in FRAM: {current_value:.2f}%")
except Exception as e:
    print(f"Error reading current value: {e}")
    current_value = 0.0

# Write new value to FRAM
try:
    success = write_filter_percent_fram(FILTER_PERCENTAGE)
    if success:
        print(f"✓ Successfully wrote {FILTER_PERCENTAGE}% to FRAM")
    else:
        print("✗ Failed to write to FRAM")
        raise Exception("FRAM write failed")
except Exception as e:
    print(f"✗ Error writing to FRAM: {e}")
    raise

# Verify the write by reading back
try:
    verify_value = read_filter_percent_fram()
    print(f"Verification - read back from FRAM: {verify_value:.2f}%")
    
    if abs(verify_value - FILTER_PERCENTAGE) < 0.01:
        print("✓ Write verification successful!")
    else:
        print("✗ Write verification failed!")
        print(f"Expected: {FILTER_PERCENTAGE}%, Got: {verify_value:.2f}%")
except Exception as e:
    print(f"✗ Error during verification: {e}")

print("Filter value set complete!") 