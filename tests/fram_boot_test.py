#!/usr/bin/env python3
"""
Test script to verify FRAM filter percentage reading on boot
and that data directory dependency has been removed.
"""

import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_fram_boot_sequence():
    """Test the boot sequence filter percentage reading"""
    print("=== FRAM Boot Test ===")
    
    # Test 1: Check that data directory doesn't exist
    print("\n1. Checking data directory removal...")
    if os.path.exists("data"):
        print("✗ Data directory still exists")
        return False
    else:
        print("✓ Data directory has been removed")
    
    # Test 2: Check that boot.py doesn't import os
    print("\n2. Checking boot.py imports...")
    try:
        with open("boot.py", "r") as f:
            boot_content = f.read()
        
        if "import os" in boot_content:
            print("✗ boot.py still imports os module")
            return False
        else:
            print("✓ boot.py no longer imports os module")
    except Exception as e:
        print(f"✗ Error reading boot.py: {e}")
        return False
    
    # Test 3: Check that main.py doesn't import os
    print("\n3. Checking main.py imports...")
    try:
        with open("main.py", "r") as f:
            main_content = f.read()
        
        if "import os" in main_content:
            print("✗ main.py still imports os module")
            return False
        else:
            print("✓ main.py no longer imports os module")
    except Exception as e:
        print(f"✗ Error reading main.py: {e}")
        return False
    
    # Test 4: Check that boot.py only uses FRAM for filter reading
    print("\n4. Checking boot.py FRAM-only filter reading...")
    try:
        if "data/filter.txt" in boot_content:
            print("✗ boot.py still references data/filter.txt")
            return False
        elif "read_filter_percent_fram()" in boot_content:
            print("✓ boot.py uses read_filter_percent_fram()")
        else:
            print("✗ boot.py doesn't use read_filter_percent_fram()")
            return False
    except Exception as e:
        print(f"✗ Error checking boot.py content: {e}")
        return False
    
    # Test 5: Check that main.py only uses FRAM for filter reading
    print("\n5. Checking main.py FRAM-only filter reading...")
    try:
        if "data/filter.txt" in main_content:
            print("✗ main.py still references data/filter.txt")
            return False
        elif "read_filter_percent_fram()" in main_content:
            print("✓ main.py uses read_filter_percent_fram()")
        else:
            print("✗ main.py doesn't use read_filter_percent_fram()")
            return False
    except Exception as e:
        print(f"✗ Error checking main.py content: {e}")
        return False
    
    # Test 6: Check that boot.py initializes filter to 0 if FRAM read fails
    print("\n6. Checking boot.py FRAM fallback logic...")
    try:
        if "write_filter_percent_fram(0.0)" in boot_content:
            print("✓ boot.py initializes filter to 0.0 in FRAM if read fails")
        else:
            print("✗ boot.py doesn't initialize filter to 0.0 in FRAM if read fails")
            return False
    except Exception as e:
        print(f"✗ Error checking boot.py fallback logic: {e}")
        return False
    
    print("\n=== All Tests Passed! ===")
    print("✓ Data directory dependency removed")
    print("✓ FRAM-only filter storage implemented")
    print("✓ Proper fallback logic for FRAM initialization")
    return True

def test_fram_initialization():
    """Test FRAM initialization and basic operations"""
    print("\n=== FRAM Initialization Test ===")
    
    try:
        from fram import init_fram, read_filter_percent_fram, write_filter_percent_fram
        
        print("1. Testing FRAM initialization...")
        success = init_fram()
        if success:
            print("✓ FRAM initialized successfully")
        else:
            print("✗ FRAM initialization failed")
            return False
        
        print("2. Testing FRAM write operation...")
        test_value = 25.5
        write_success = write_filter_percent_fram(test_value)
        if write_success:
            print(f"✓ Wrote {test_value}% to FRAM")
        else:
            print(f"✗ Failed to write {test_value}% to FRAM")
            return False
        
        print("3. Testing FRAM read operation...")
        read_value = read_filter_percent_fram()
        if abs(read_value - test_value) < 0.01:
            print(f"✓ Read {read_value}% from FRAM (matches written value)")
        else:
            print(f"✗ Read {read_value}% from FRAM (expected {test_value}%)")
            return False
        
        print("4. Testing FRAM reset to 0...")
        write_filter_percent_fram(0.0)
        reset_value = read_filter_percent_fram()
        if reset_value == 0.0:
            print("✓ FRAM reset to 0.0% successfully")
        else:
            print(f"✗ FRAM reset failed, got {reset_value}%")
            return False
        
        print("\n=== FRAM Tests Passed! ===")
        return True
        
    except ImportError as e:
        print(f"✗ Could not import FRAM module: {e}")
        return False
    except Exception as e:
        print(f"✗ FRAM test error: {e}")
        return False

if __name__ == "__main__":
    print("FRAM Boot Test Suite")
    print("===================")
    
    # Run boot sequence tests
    boot_tests_passed = test_fram_boot_sequence()
    
    # Run FRAM initialization tests
    fram_tests_passed = test_fram_initialization()
    
    if boot_tests_passed and fram_tests_passed:
        print("\n🎉 All tests passed! The system is ready for FRAM-only operation.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1) 