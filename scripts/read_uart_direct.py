import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl stop arduino-router")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline('cat << "PY" > ~/read_uart_direct.py\n'
'import serial, time\n'
'try:\n'
'    ser = serial.Serial(\'/dev/ttyHS1\', 115200, timeout=1)\n'
'    print(\'=== READING RAW UART ===\')\n'
'    start = time.time()\n'
'    count = 0\n'
'    while time.time() - start < 5 and count < 10:\n'
'        line = ser.readline().decode(\'utf-8\', errors=\'ignore\').strip()\n'
'        if line:\n'
'            print(\'RAW:\', line)\n'
'            count += 1\n'
'    ser.close()\n'
'except Exception as e:\n'
'    print(\'Err:\', e)\n'
'PY\n')
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("python3 ~/read_uart_direct.py")
child.expect([r'arduino@blissy:\~\$ '], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
