import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Stop arduino-router so we have exclusive raw ownership of /dev/ttyHS1
child.sendline("echo 'Askaban78@#' | sudo -S systemctl stop arduino-router")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Release GPIO reset line to run sketch
child.sendline("sudo /usr/bin/gpioset -c /dev/gpiochip1 -t0 70=1")
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=15)

# Read live stream directly from /dev/ttyHS1
child.sendline('python3 -c "\n'
'import serial, time\n'
'try:\n'
'    ser = serial.Serial(\'/dev/ttyHS1\', 115200, timeout=1)\n'
'    print(\'=== READING LIVE BNO08X ORIENTATION STREAM FROM ttyHS1 ===\')\n'
'    start = time.time()\n'
'    count = 0\n'
'    while time.time() - start < 10 and count < 10:\n'
'        line = ser.readline().decode(\'utf-8\', errors=\'ignore\').strip()\n'
'        if line:\n'
'            print(\'RAW:\', line)\n'
'        if line.startswith(\'Q,\'):\n'
'            parts = line.split(\',\')\n'
'            if len(parts) >= 5:\n'
'                print(f\'Sample {count+1} -> Quat(w={parts[1]}, x={parts[2]}, y={parts[3]}, z={parts[4]})\')\n'
'                count += 1\n'
'    ser.close()\n'
'except Exception as e:\n'
'    print(\'Error reading:\', e)\n'
'"')
child.expect([r'arduino@blissy:\~\$', r'\$'], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
