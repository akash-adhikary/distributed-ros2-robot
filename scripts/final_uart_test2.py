import pexpect, sys

bash_script = """
set -e
cat << "SKETCH" > ~/BnoTest/BnoTest.ino
void setup() {
  Serial1.begin(115200);
  delay(100);
  Serial1.println("HELLO WORLD FROM UNO Q MCU!");
}
void loop() {
  Serial1.println("ALIVE_TEST");
  delay(500);
}
SKETCH
echo "Compiling..."
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo "Uploading..."
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null

echo "Killing gpioset..."
echo 'Askaban78@#' | sudo -S killall gpioset || true

echo "Stopping router..."
echo 'Askaban78@#' | sudo -S systemctl stop arduino-router

cat << "PY" > ~/read_uart_direct.py
import serial, time, os
try:
    ser = serial.Serial()
    ser.port = '/dev/ttyHS1'
    ser.baudrate = 115200
    ser.timeout = 1
    ser.dtr = False
    ser.rts = False
    ser.open()
    ser.dtr = False
    ser.rts = False
    
    # Pulse the wakeup GPIO after the port is open and DTR is false!
    os.system("echo 'Askaban78@#' | sudo -S /usr/bin/gpioset -c /dev/gpiochip1 -t0 37=0")
    time.sleep(0.1)
    os.system("echo 'Askaban78@#' | sudo -S /usr/bin/gpioset -c /dev/gpiochip1 -t0 70=1")
    
    print('=== READING RAW UART ===')
    start = time.time()
    count = 0
    while time.time() - start < 5 and count < 10:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            print('RAW:', line)
            count += 1
    ser.close()
except Exception as e:
    print('Err:', e)
PY

echo "Running python read..."
python3 ~/read_uart_direct.py
echo "ALL_DONE"
"""

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:'], timeout=15)

child.sendline("cat << 'REMOTE_SCRIPT' > ~/run_test.sh\n" + bash_script + "\nREMOTE_SCRIPT\n")
child.expect([r'arduino@blissy:'], timeout=15)

child.sendline("bash ~/run_test.sh")
child.expect([r'ALL_DONE'], timeout=120)

child.sendline("exit")
child.expect(pexpect.EOF)
