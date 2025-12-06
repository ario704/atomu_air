#!/usr/bin/env python3
"""
Basic FRAM test to verify write and read operations
"""

from machine import Pin
import utime as time
from fram import init_fram, write_filter_percent_fram, read_filter_percent_fram

def test_fram_basic():
    """Test basic FRAM write and read operations"""
    print("=== Basic FRAM Test ===")
    
    # Initialize FRAM
    print("1. Initializing FRAM...")
    if not init_fram():
        print("✗ FRAM initialization failed")
        return False
    print("✓ FRAM initialized")
    
    # Test writing and reading different values
    test_values = [0.0, 25.5, 50.0, 75.25, 100.0]
    
    for i, test_value in enumerate(test_values):
        print(f"2.{i+1}. Testing value: {test_value:.2f}%")
        
        # Write value
        write_success = write_filter_percent_fram(test_value)
        if not write_success:
            print(f"   ✗ Failed to write {test_value:.2f}%")
            return False
        
        # Small delay
        time.sleep(0.1)
        
        # Read value back
        read_value = read_filter_percent_fram()
        print(f"   - Wrote: {test_value:.2f}%, Read: {read_value:.2f}%")
        
        # Check if values match (with small tolerance for float precision)
        if abs(read_value - test_value) < 0.01:
            print(f"   ✓ Values match")
        else:
            print(f"   ✗ Values don't match (difference: {abs(read_value - test_value):.4f})")
            return False
    
    print("3. Testing edge cases...")
    
    # Test negative value (should clamp to 0)
    write_filter_percent_fram(-10.0)
    time.sleep(0.1)
    value = read_filter_percent_fram()
    if value == 0.0:
        print("   ✓ Negative value clamped to 0.0")
    else:
        print(f"   ✗ Negative value not clamped: {value}")
        return False
    
    # Test value over 100 (should clamp to 100)
    write_filter_percent_fram(150.0)
    time.sleep(0.1)
    value = read_filter_percent_fram()
    if value == 100.0:
        print("   ✓ Value over 100 clamped to 100.0")
    else:
        print(f"   ✗ Value over 100 not clamped: {value}")
        return False
    
    print("✓ All FRAM tests passed")
    return True

if __name__ == "__main__":
    success = test_fram_basic()
    if success:
        print("\n=== Test PASSED ===")
    else:
        print("\n=== Test FAILED ===") 