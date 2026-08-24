import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline('python3 -c "\n'
'import serial, time\n'
'ser = serial.Serial(\'/dev/ttyHS1\', 115200, timeout=1)\n'
'print(\'--- LISTENING TO DIRECT MCU SERIAL STREAM ---\')\n'
'start = time.time()\n'
'while time.time() - start < 5:\n'
'    line = ser.readline().decode(\'utf-8\', errors=\'ignore\').strip()\n'
'    if line:\n'
'        print(\'IMU ->\', line)\n'
'ser.close()\n'
'"')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
