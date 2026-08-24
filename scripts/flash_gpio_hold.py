import pexpect, sys

bash_script = """
set -e
cat << "PY" > ~/read_uart_hold.py
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
    print('=== RAW UART, GPIO HELD ===')
    start = time.time()
    count = 0
    # Hold the MCU awake for 10 seconds by keeping 70=1
    os.system("sudo /usr/bin/gpioset -c /dev/gpiochip1 -p 10000 70=1 &")
    time.sleep(0.5)
    while time.time() - start < 8 and count < 10:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            print('RAW:', line)
            count += 1
    ser.close()
except Exception as e:
    print('Err:', e)
PY
echo 'Askaban78@#' | sudo -S systemctl stop arduino-router
echo "Waking MCU and running Python..."
python3 ~/read_uart_hold.py
"""

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:'], timeout=15)

child.sendline("cat << 'REMOTE_SCRIPT' > ~/run_test.sh\n" + bash_script + "\nREMOTE_SCRIPT\n")
child.expect([r'arduino@blissy:'], timeout=15)

child.sendline("bash ~/run_test.sh")
child.expect([r'RAW UART, GPIO HELD'], timeout=60)
child.expect([r'arduino@blissy:'], timeout=30)

child.sendline("exit")
child.expect(pexpect.EOF)
