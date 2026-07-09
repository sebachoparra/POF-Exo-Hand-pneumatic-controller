import time
import struct
import smbus

# BNO055 Default I2C Address and Registers
BNO055_ADDRESS = 0x28
BNO055_OP_MODE_REG = 0x3D
BNO055_EULER_DATA_START = 0x1A

# Operation Modes
MODE_CONFIG = 0x00
MODE_NDOF = 0x0C  # 9-axis absolute orientation fusion mode

# Initialize built-in I2C bus 1
bus = smbus.SMBus(1)

def init_bno():
    # Switch to config mode to make changes
    bus.write_byte_data(BNO055_ADDRESS, BNO055_OP_MODE_REG, MODE_CONFIG)
    time.sleep(0.05)
    # Set to NDOF mode (turns on accelerometer, gyro, and magnetometer fusion)
    bus.write_byte_data(BNO055_ADDRESS, BNO055_OP_MODE_REG, MODE_NDOF)
    time.sleep(0.05)
    print("BNO055 Initialized Successfully!")

def read_euler():
    # Read 6 bytes of Euler data (2 bytes each for Heading, Roll, Pitch)
    data = bus.read_i2c_block_data(BNO055_ADDRESS, BNO055_EULER_DATA_START, 6)
    
    # Unpack 3 signed short integers (little-endian)
    heading, roll, pitch = struct.unpack('<hhh', bytes(data))
    
    # BNO055 outputs 1 degree per 16 LSB
    return heading / 16.0, roll / 16.0, pitch / 16.0

# Run the program
try:
    init_bno()
    while True:
        h, r, p = read_euler()
        print(f"InclinaçãoXY: {h:6.2f}° | InclinaçãoZY: {-r:6.2f}° | InclinaçãoXZ: {p:6.2f}°")
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nStopped.")
