import serial
import time

port = '/dev/ttyUSB0'
baud = 460800

print(f"Opening port {port} at {baud}...")
try:
    ser = serial.Serial(port, baud, timeout=2.0)
    time.sleep(1.0)
    
    # 1. Send stop command first to clear any state (0xA5 0x25)
    print("Sending Stop command...")
    ser.write(b'\xA5\x25')
    ser.flush()
    time.sleep(0.5)
    
    # 2. Send Start Scan command (0xA5 0x20)
    print("Sending Start Scan command (0xA5 0x20)...")
    ser.write(b'\xA5\x20')
    ser.flush()
    
    print("Waiting 10 seconds. Check if motor starts spinning!")
    time.sleep(10.0)
    
    # 3. Stop scan
    print("Sending Stop command...")
    ser.write(b'\xA5\x25')
    ser.flush()
    
    ser.close()
    print("Finished.")
except Exception as e:
    print(f"❌ ERROR: {e}")
