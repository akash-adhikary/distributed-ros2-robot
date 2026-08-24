import pexpect, sys

bash_script = """
set -e
cat << "SKETCH" > ~/BnoTest/BnoTest.ino
void setup() {
  Serial1.begin(115200);
  delay(1000);
  Serial1.println("HELLO WORLD FROM UNO Q MCU!");
}
void loop() {
  Serial1.println("ALIVE");
  delay(1000);
}
SKETCH
echo "Compiling..."
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo "Uploading..."
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo "Restarting router..."
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2
echo "Stopping router..."
sudo systemctl stop arduino-router
cat << "PY" > ~/read_uart_direct.py
import serial, time
try:
    ser = serial.Serial('/dev/ttyHS1', 115200, timeout=1)
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
