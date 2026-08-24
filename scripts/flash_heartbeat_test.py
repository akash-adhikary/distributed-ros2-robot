import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Write simple heartbeat test on Serial1 & Serial
child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'void setup() {\n'
'  Serial1.begin(115200);\n'
'}\n'
'void loop() {\n'
'  Serial1.println("HEARTBEAT_OK");\n'
'  delay(200);\n'
'}\n'
'SKETCH\n')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=120)

child.sendline('python3 -c "\n'
'import serial, time\n'
'ser = serial.Serial(\'/dev/ttyHS1\', 115200, timeout=1)\n'
'for i in range(10):\n'
'    line = ser.readline().decode(\'utf-8\', errors=\'ignore\').strip()\n'
'    if line:\n'
'        print(\'UART RECEIVED:\', line)\n'
'ser.close()\n'
'"')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
