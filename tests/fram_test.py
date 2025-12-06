#!/usr/bin/env python3
"""
Test script for MB85RC04PNF FRAM chip
Tests basic read/write functionality
"""

import sys
import os
sys.path.append('..')

from fram import init_fram, read_filter_percent_fram, write_filter_percent_fram, fram

def test_fram():
    print("=== FRAM Test ===")
    
    # Test initialization
    print("1. Testing FRAM initialization...")
    if init_fram():
        print("   ✓ FRAM initialized successfully")
    else:
        print("   ✗ FRAM initialization failed")
        return False
    
    # Test write and read
    print("2. Testing write/read operations...")
    test_value = 42
    print(f"   Writing value: {test_value}")
    
    if write_filter_percent_fram(test_value):
        print("   ✓ Write successful")
    else:
        print("   ✗ Write failed")
        return False
    
    # Read back the value
    read_value = read_filter_percent_fram()
    print(f"   Read value: {read_value}")
    
    if read_value == test_value:
        print("   ✓ Read/write test passed")
    else:
        print(f"   ✗ Read/write test failed: expected {test_value}, got {read_value}")
        return False
    
    # Test edge cases
    print("3. Testing edge cases...")
    
    # Test value 0
    write_filter_percent_fram(0)
    if read_filter_percent_fram() == 0:
        print("   ✓ Zero value test passed")
    else:
        print("   ✗ Zero value test failed")
        return False
    
    # Test value 100
    write_filter_percent_fram(100)
    if read_filter_percent_fram() == 100:
        print("   ✓ Max value test passed")
    else:
        print("   ✗ Max value test failed")
        return False
    
    # Test out of range values (should be clamped)
    write_filter_percent_fram(150)
    if read_filter_percent_fram() == 100:
        print("   ✓ Out of range clamping test passed")
    else:
        print("   ✗ Out of range clamping test failed")
        return False
    
    write_filter_percent_fram(-10)
    if read_filter_percent_fram() == 0:
        print("   ✓ Negative value clamping test passed")
    else:
        print("   ✗ Negative value clamping test failed")
        return False
    
    # Test direct FRAM operations
    print("4. Testing direct FRAM operations...")
    try:
        # Write a test pattern
        fram.write_int(4, 0x12345678)
        read_val = fram.read_int(4)
        if read_val == 0x12345678:
            print("   ✓ Direct FRAM operations test passed")
        else:
            print(f"   ✗ Direct FRAM operations test failed: expected 0x12345678, got 0x{read_val:08x}")
            return False
    except Exception as e:
        print(f"   ✗ Direct FRAM operations test failed: {e}")
        return False
    
    print("\n=== All tests passed! ===")
    return True

if __name__ == "__main__":
    success = test_fram()
    if not success:
        print("\n=== Some tests failed ===")
        sys.exit(1) 