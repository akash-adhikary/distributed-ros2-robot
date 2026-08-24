import pexpect, sys

bash_script = """
set -e
rm -f ~/BnoTest/*.ino
cat << "SKETCH" > ~/BnoTest/BnoTest.ino
void setup() {
  Serial1.begin(115200);
  delay(1000);
  Serial1.println("UART BYPASS START");
}
void loop() {
  Serial1.println("UART BYPASS LOOP");
  delay(1000);
}
SKETCH
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo 'Askaban78@#' | sudo -S systemctl stop arduino-router
cat << "PY" > ~/read_uart_dtr.py
import serial, time
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
    print('=== RAW UART, DTR/RTS FALSE ===')
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
# Execute the wakeup pulse BEFORE python starts OR let Python start and then pulse it!
echo "Waking MCU and running Python..."
sudo /usr/bin/gpioset -c /dev/gpiochip1 -t0 70=1 &
python3 ~/read_uart_dtr.py
"""

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:'], timeout=15)

child.sendline("cat << 'REMOTE_SCRIPT' > ~/run_test.sh\n" + bash_script + "\nREMOTE_SCRIPT\n")
child.expect([r'arduino@blissy:'], timeout=15)

child.sendline("bash ~/run_test.sh")
child.expect([r'RAW UART, DTR/RTS FALSE'], timeout=120)
child.expect([r'arduino@blissy:'], timeout=30)

child.sendline("exit")
child.expect(pexpect.EOF)
