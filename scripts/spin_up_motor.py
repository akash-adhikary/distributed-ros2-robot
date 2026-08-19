import serial
import time

port = '/dev/ttyUSB0'
baud = 460800

print(f"Opening port {port} at {baud}...")
try:
    ser = serial.Serial(port, baud, timeout=2.0)
    time.sleep(1.0)
    
    # Send Start Scan command (0xA5 0x20) to spin the motor
    print("Sending Start Scan command (0xA5 0x20) to spin up the motor...")
    ser.write(b'\xA5\x20')
    ser.flush()
    
    print("Waiting 4 seconds for motor to reach full speed...")
    time.sleep(4.0)
    
    # Close port without stopping the motor
    ser.close()
    print("Port closed. Motor should still be spinning!")
    print("Now immediately run the ROS 2 driver command!")
except Exception as e:
    print(f"❌ ERROR: {e}")
