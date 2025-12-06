from machine import I2C, Pin
import time

class MB85RC04PNF:
    """
    Driver for MB85RC04PNF FRAM chip
    4Kbit (512 bytes) non-volatile memory
    I2C address: 0x50 (with A0-A2 pins grounded)
    """
    
    def __init__(self, i2c, address=0x50):
        self.i2c = i2c
        self.address = address
        self.size = 512  # 4Kbit = 512 bytes
        
    def read_byte(self, address):
        """Read a single byte from FRAM"""
        if address >= self.size:
            raise ValueError(f"Address {address} out of range (0-{self.size-1})")
        
        # Send 2-byte address (big-endian)
        addr_bytes = address.to_bytes(2, 'big')
        data = self.i2c.readfrom_mem(self.address, addr_bytes[0] << 8 | addr_bytes[1], 1)
        return data[0] if data else 0
    
    def write_byte(self, address, value):
        """Write a single byte to FRAM"""
        if address >= self.size:
            raise ValueError(f"Address {address} out of range (0-{self.size-1})")
        
        # Send 2-byte address (big-endian) followed by data
        addr_bytes = address.to_bytes(2, 'big')
        self.i2c.writeto_mem(self.address, addr_bytes[0] << 8 | addr_bytes[1], bytes([value]))
    
    def read_bytes(self, address, length):
        """Read multiple bytes from FRAM"""
        if address + length > self.size:
            raise ValueError(f"Read range {address}-{address+length-1} out of range (0-{self.size-1})")
        
        # Send 2-byte address (big-endian)
        addr_bytes = address.to_bytes(2, 'big')
        data = self.i2c.readfrom_mem(self.address, addr_bytes[0] << 8 | addr_bytes[1], length)
        return data
    
    def write_bytes(self, address, data):
        """Write multiple bytes to FRAM"""
        if address + len(data) > self.size:
            raise ValueError(f"Write range {address}-{address+len(data)-1} out of range (0-{self.size-1})")
        
        # Send 2-byte address (big-endian) followed by data
        addr_bytes = address.to_bytes(2, 'big')
        self.i2c.writeto_mem(self.address, addr_bytes[0] << 8 | addr_bytes[1], data)
    
    def read_int(self, address):
        """Read a 32-bit integer from FRAM"""
        data = self.read_bytes(address, 4)
        return int.from_bytes(data, 'little')
    
    def write_int(self, address, value):
        """Write a 32-bit integer to FRAM"""
        data = value.to_bytes(4, 'little')
        self.write_bytes(address, data)
    
    def read_float(self, address):
        """Read a 32-bit float from FRAM"""
        data = self.read_bytes(address, 4)
        import struct
        return struct.unpack('f', data)[0]
    
    def write_float(self, address, value):
        """Write a 32-bit float to FRAM"""
        import struct
        data = struct.pack('f', value)
        self.write_bytes(address, data)
    
    def test_connection(self):
        """Test if FRAM is responding"""
        try:
            # Try to read from address 0
            self.read_byte(0)
            return True
        except Exception as e:
            print(f"FRAM connection test failed: {e}")
            return False

# Global FRAM instance
fram = None

def init_fram():
    """Initialize FRAM with I2C on pins GP16 (SDA) and GP17 (SCL)"""
    global fram
    try:
        print("Creating I2C0 on GP16/GP17...")
        i2c = I2C(0, sda=Pin(16), scl=Pin(17), freq=100000)  # 100kHz for reliability
        print("I2C0 created successfully")
        
        print("Scanning for I2C devices...")
        devices = i2c.scan()
        print(f"Found {len(devices)} device(s): {[hex(d) for d in devices]}")
        
        if 0x50 not in devices:
            print("FRAM not found at address 0x50")
            return False
        
        print("Creating FRAM instance...")
        fram = MB85RC04PNF(i2c, address=0x50)
        
        print("Testing FRAM connection...")
        if fram.test_connection():
            print("FRAM initialized successfully")
            return True
        else:
            print("FRAM connection test failed")
            return False
    except Exception as e:
        print(f"Failed to initialize FRAM: {e}")
        return False

def read_filter_percent_fram():
    """Read filter percentage from FRAM (with decimal precision)"""
    global fram
    if fram is None:
        print("FRAM not initialized, returning 0")
        return 0.0
    
    try:
        # Read from address 0 as float
        value = fram.read_float(0)
        # Validate the value is reasonable (0-100)
        if 0.0 <= value <= 100.0:
            return value
        else:
            print(f"Invalid filter percent in FRAM: {value}, resetting to 0")
            write_filter_percent_fram(0.0)
            return 0.0
    except Exception as e:
        print(f"Error reading from FRAM: {e}, returning 0")
        return 0.0

def write_filter_percent_fram(value):
    """Write filter percentage to FRAM (with decimal precision)"""
    global fram
    if fram is None:
        print("FRAM not initialized, cannot write")
        return False
    
    try:
        # Ensure value is in valid range
        value = max(0.0, min(100.0, float(value)))
        print(f"[DEBUG] Writing {value:.2f}% to FRAM...")
        
        # Write to address 0 as float
        fram.write_float(0, value)
        
        # Verify the write by reading back immediately
        time.sleep(0.01)  # Small delay to ensure write completes
        verify_value = fram.read_float(0)
        print(f"[DEBUG] Write verification: wrote {value:.2f}%, read back {verify_value:.2f}%")
        
        if abs(verify_value - value) < 0.01:
            print(f"✓ Filter percent {value:.2f}% written to FRAM and verified")
            return True
        else:
            print(f"✗ Write verification failed: wrote {value:.2f}%, read back {verify_value:.2f}%")
            return False
    except Exception as e:
        print(f"Error writing to FRAM: {e}")
        return False 