import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl restart arduino-router")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("arduino-cli compile -v --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=180)

child.sendline("arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=120)

child.sendline("echo 'Askaban78@#' | sudo -S systemctl stop arduino-router")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline("sudo /usr/bin/gpioset -c /dev/gpiochip1 -t0 70=1")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

child.sendline('python3 -c "\n'
'import serial, time\n'
'ser = serial.Serial(\'/dev/ttyHS1\', 115200, timeout=1)\n'
'print(\'=== READING LIVE BNO08X ORIENTATION STREAM FROM ttyHS1 ===\')\n'
'start = time.time()\n'
'count = 0\n'
'while time.time() - start < 10 and count < 10:\n'
'    try:\n'
'        line = ser.readline().decode(\'utf-8\', errors=\'ignore\').strip()\n'
'        if line.startswith(\'Q,\'):\n'
'            parts = line.split(\',\')\n'
'            if len(parts) >= 5:\n'
'                print(f\'Sample {count+1} -> Quat(w={parts[1]}, x={parts[2]}, y={parts[3]}, z={parts[4]})\')\n'
'                count += 1\n'
'    except Exception as e:\n'
'        print(\'Error reading:\', e)\n'
'ser.close()\n'
'"')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
